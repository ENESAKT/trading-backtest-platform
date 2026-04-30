"""Telegram long polling dinleyicisi.

Bot'a gelen mesajları dinler, chat_id doğrular, rate limit uygular
ve komut işleyicisine yönlendirir.

Güvenlik garantileri:
  - Yalnızca TELEGRAM_CHAT_ID'den gelen mesajlar işlenir.
  - Başka chat_id: "Yetkisiz erişim" yanıtı döner.
  - Token ve gizli bilgiler asla Telegram'a yazılmaz.
  - Komut başına 5s cooldown, saatlik 60 mesaj limiti.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from backend.config import getenv, llm_configured, telegram_authorized_chat_configured
from backend.notifier.listener_status import write_listener_status

logger = logging.getLogger(__name__)

# Rate limit sabitleri
HOURLY_LIMIT = 60
CMD_COOLDOWN_SECONDS = 5
ERROR_COOLDOWN_SECONDS = 300


# ── Rate limiter ──────────────────────────────────────────────────────────────

class _RateLimiter:
    def __init__(self) -> None:
        self._cmd_last: dict[str, float] = {}
        self._error_until: dict[str, float] = {}
        self._hourly_count = 0
        self._hourly_reset = time.monotonic() + 3600

    def check_command(self, cmd: str) -> tuple[bool, str]:
        """(ok, red_sebebi) döner."""
        now = time.monotonic()
        if now > self._hourly_reset:
            self._hourly_count = 0
            self._hourly_reset = now + 3600
        if self._hourly_count >= HOURLY_LIMIT:
            return False, f"Saatlik mesaj limiti ({HOURLY_LIMIT}) aşıldı."
        last = self._cmd_last.get(cmd, 0.0)
        remaining = CMD_COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            return False, f"`{cmd}` için {int(remaining) + 1}s bekleyin."
        return True, ""

    def record_command(self, cmd: str) -> None:
        self._cmd_last[cmd] = time.monotonic()
        self._hourly_count += 1

    def allow_error(self, error_key: str) -> bool:
        """True ise hatayı gönder, False ise sustur (spam önleme)."""
        now = time.monotonic()
        if now < self._error_until.get(error_key, 0.0):
            return False
        self._error_until[error_key] = now + ERROR_COOLDOWN_SECONDS
        return True


_limiter = _RateLimiter()
_offset: int = 0

# Asistan durum kaydı (API endpoint için)
_listener_durum: dict[str, Any] = {
    "aktif": False,
    "islenen_mesaj": 0,
    "son_mesaj": None,
    "son_hata": None,
}


def get_listener_status() -> dict[str, Any]:
    return dict(_listener_durum)


def _publish_status() -> None:
    try:
        write_listener_status(_listener_durum)
    except Exception as exc:  # noqa: BLE001
        logger.debug("telegram_listener: durum yazılamadı — %s", exc)


# ── Telegram API yardımcıları ──────────────────────────────────────────────────

async def _get_updates(offset: int, timeout: int = 30) -> list[dict[str, Any]]:
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return []
    try:
        async with httpx.AsyncClient(timeout=timeout + 5) as client:
            r = await client.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": offset, "timeout": timeout, "limit": 10},
            )
        if r.status_code != 200:
            logger.warning("telegram_listener: getUpdates HTTP %d", r.status_code)
            return []
        data = r.json()
        if not data.get("ok"):
            logger.warning("telegram_listener: getUpdates not ok — %s", data)
            return []
        return data.get("result", [])
    except Exception as exc:  # noqa: BLE001
        logger.debug("telegram_listener: getUpdates hatası — %s", exc)
        return []


def _as_command_reply(text: str) -> str:
    return f"🏷 *Komut cevabı*\n{text}"


async def _send(chat_id: str | int, text: str) -> None:
    """Mesaj gönder; token yoksa sessizce geç."""
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    text = _as_command_reply(text)
    # Telegram 4096 karakter sınırı
    if len(text) > 4096:
        text = text[:4000] + "\n…_(mesaj kısaltıldı)_"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram_listener: yanıt gönderilemedi — %s", exc)


# ── Mesaj işleme ───────────────────────────────────────────────────────────────

def _parse_command(text: str) -> tuple[str, str]:
    """'/komut argümanlar' → ('/komut', 'argümanlar')."""
    text = text.strip()
    if not text.startswith("/"):
        return "", text
    parts = text.split(None, 1)
    # Grup botlarında '@BotAdi' ekini temizle
    cmd = parts[0].split("@")[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


async def _handle_update(update: dict[str, Any]) -> None:
    global _offset
    _offset = update["update_id"] + 1

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str(message.get("chat", {}).get("id", ""))
    text = (message.get("text") or "").strip()
    if not text:
        return

    allowed_chat_id = getenv("TELEGRAM_CHAT_ID")

    # ── Yetki kontrolü ──────────────────────────────────────────────────────
    if not allowed_chat_id:
        logger.warning(
            "telegram_listener: yetkili Telegram kullanıcısı yapılandırılmamış, mesaj reddedildi"
        )
        return

    if chat_id != allowed_chat_id:
        logger.warning("telegram_listener: yetkisiz erişim girişimi engellendi")
        await _send(chat_id, "⛔ Yetkisiz erişim.")
        return

    _listener_durum["islenen_mesaj"] += 1

    cmd, args = _parse_command(text)
    _listener_durum["son_mesaj"] = cmd or "(serbest metin)"
    _publish_status()

    # ── Komut değil → serbest metin (LLM veya yardım) ───────────────────────
    if not cmd:
        reply = await _handle_free_text(text)
        await _send(chat_id, reply)
        return

    # ── Rate limit ───────────────────────────────────────────────────────────
    ok, reason = _limiter.check_command(cmd)
    if not ok:
        await _send(chat_id, f"⏳ {reason}")
        return

    # ── Komut dispatch ───────────────────────────────────────────────────────
    from backend.notifier.telegram_commands import COMMANDS

    handler = COMMANDS.get(cmd)
    if handler is None:
        await _send(
            chat_id,
            f"❓ Bilinmeyen komut: `{cmd}`\n/yardim ile listeyi görebilirsiniz.",
        )
        return

    _limiter.record_command(cmd)

    # Uzun komutlar için "işleniyor" bildirimi
    slow = {"/kontrol", "/gorev", "/duzelt", "/sinyal", "/strateji"}
    if cmd in slow:
        await _send(chat_id, f"⏳ `{cmd}` işleniyor…")

    try:
        reply = await asyncio.wait_for(handler(args), timeout=90)
        await _send(chat_id, reply or "✅ Tamamlandı.")
    except asyncio.TimeoutError:
        await _send(chat_id, f"⌛ `{cmd}` zaman aşımına uğradı (90s).")
    except Exception as exc:  # noqa: BLE001
        logger.exception("telegram_listener: komut hatası — %s %s", cmd, exc)
        err_key = f"cmd_{cmd}"
        if _limiter.allow_error(err_key):
            await _send(
                chat_id,
                f"❌ `{cmd}` çalışırken hata: `{type(exc).__name__}`",
            )


async def _handle_free_text(text: str) -> str:
    """Komut olmayan mesajları işle.

    ANTHROPIC_API_KEY varsa claude-haiku ile yanıtla;
    yoksa komut listesine yönlendir.
    """
    if not llm_configured():
        return (
            "💬 Serbest sohbet için `ANTHROPIC_API_KEY` gerekli.\n\n"
            "Komut listesi: /yardim"
        )

    try:
        import anthropic

        anthropic_key = getenv("ANTHROPIC_API_KEY")
        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        system_prompt = (
            "Sen PiyasaPilot trading asistanısın. "
            "Yalnızca Türkçe yanıt ver. "
            "Token, API key, şifre ve .env içeriğini asla paylaşma. "
            "Gerçek alım-satım emri verme. "
            "Yatırım tavsiyesi değildir uyarısını gerektiğinde ekle. "
            "Yanıtları kısa ve net tut (en fazla 300 kelime)."
        )
        response = await asyncio.wait_for(
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": text[:1000]}],
            ),
            timeout=30,
        )
        return response.content[0].text if response.content else "Yanıt alınamadı."

    except asyncio.TimeoutError:
        return "⌛ Yanıt zaman aşımına uğradı. Tekrar deneyin."
    except ImportError:
        return (
            "💬 `anthropic` paketi kurulu değil.\n"
            "Komut listesi: /yardim"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram_listener: LLM hatası — %s", exc)
        return "❌ Yanıt üretilemedi. Komutlar için /yardim yazın."


# ── Ana döngü ──────────────────────────────────────────────────────────────────

async def listener_loop() -> None:
    """Telegram long polling ana döngüsü.

    backend/notifier/main.py asyncio.gather() içinden başlatılır.
    """
    global _offset

    if not getenv("TELEGRAM_BOT_TOKEN"):
        logger.info(
            "telegram_listener: Telegram bot token yapılandırılmamış — listener başlatılmıyor"
        )
        _listener_durum["aktif"] = False
        _publish_status()
        return

    if not telegram_authorized_chat_configured():
        logger.warning(
            "telegram_listener: yetkili Telegram kullanıcısı yapılandırılmamış — "
            "tüm mesajlar reddedilecek"
        )

    logger.info("telegram_listener: başlatıldı (long polling)")
    _listener_durum["aktif"] = True
    _publish_status()

    reconnect_delay = 5

    while True:
        try:
            updates = await _get_updates(_offset, timeout=30)
            reconnect_delay = 5  # başarılı yanıtta sıfırla
            _publish_status()

            for update in updates:
                try:
                    await _handle_update(update)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "telegram_listener: update işleme hatası — %s", exc
                    )
                    _listener_durum["son_hata"] = str(exc)[:200]

        except asyncio.CancelledError:
            _listener_durum["aktif"] = False
            _publish_status()
            logger.info("telegram_listener: durduruldu")
            return
        except Exception as exc:  # noqa: BLE001
            _listener_durum["son_hata"] = str(exc)[:200]
            _publish_status()
            logger.warning(
                "telegram_listener: döngü hatası — %s, %ds sonra yeniden denenecek",
                exc,
                reconnect_delay,
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)

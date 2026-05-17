"""Telegram bildirim modülü.

Tüm bildirimler .env dosyasındaki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID
değişkenlerinden okunur. Token hiçbir zaman kod içine yazılmaz.

Desteklenen olaylar:
  - Bot başlatıldı / durduruldu
  - Yeni sinyal
  - Alım / satım notu
  - Günlük zarar limiti aşıldı (cüzdan donduruldu)
  - Hata
  - Günlük özet
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

from backend.config import ROOT, getenv, telegram_configured

logger = logging.getLogger(__name__)

_LIFECYCLE_COOLDOWN_SECONDS = 60
_LIFECYCLE_GUARD_PATH = ROOT / "data" / "runtime" / "telegram_lifecycle_guard.json"
_SIGNAL_COOLDOWN_PATH = ROOT / "data" / "runtime" / "telegram_signal_cooldown.json"


def _configured() -> bool:
    if not telegram_configured():
        logger.warning(
            "telegram: Telegram bildirimi yapılandırılmamış"
        )
        return False
    return True


def _with_source(text: str, source: str | None) -> str:
    if not source:
        return text
    return f"🏷 *{source}*\n{text}"


def _lifecycle_allowed(
    event: str,
    now: dt.datetime | None = None,
    guard_path: Any | None = None,
) -> bool:
    """Aynı yaşam döngüsü bildirimini kısa sürede tekrar gönderme."""
    current = now or dt.datetime.now(dt.timezone.utc)
    path = guard_path or _LIFECYCLE_GUARD_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:  # noqa: BLE001
        data = {}

    last_raw = data.get(event)
    if last_raw:
        try:
            last = dt.datetime.fromisoformat(last_raw)
            if last.tzinfo is None:
                last = last.replace(tzinfo=dt.timezone.utc)
            age = (current - last.astimezone(dt.timezone.utc)).total_seconds()
            if age < _LIFECYCLE_COOLDOWN_SECONDS:
                return False
        except Exception:  # noqa: BLE001
            pass

    data[event] = current.replace(microsecond=0).isoformat()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return True


def _in_quiet_hours(quiet_hours: str, now: dt.datetime | None = None) -> bool:
    if not quiet_hours or "-" not in quiet_hours:
        return False
    start_raw, end_raw = [part.strip() for part in quiet_hours.split("-", 1)]
    try:
        start_h, start_m = [int(part) for part in start_raw.split(":", 1)]
        end_h, end_m = [int(part) for part in end_raw.split(":", 1)]
    except ValueError:
        return False
    current = now or dt.datetime.now()
    current_minutes = current.hour * 60 + current.minute
    start = start_h * 60 + start_m
    end = end_h * 60 + end_m
    if start == end:
        return False
    if start < end:
        return start <= current_minutes < end
    return current_minutes >= start or current_minutes < end


def _cooldown_allowed(key: str, minutes: int) -> bool:
    if minutes <= 0:
        return True
    now = dt.datetime.now(dt.timezone.utc)
    try:
        _SIGNAL_COOLDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = (
            json.loads(_SIGNAL_COOLDOWN_PATH.read_text(encoding="utf-8"))
            if _SIGNAL_COOLDOWN_PATH.exists()
            else {}
        )
    except Exception:
        data = {}

    last_raw = data.get(key)
    if last_raw:
        try:
            last = dt.datetime.fromisoformat(last_raw)
            if last.tzinfo is None:
                last = last.replace(tzinfo=dt.timezone.utc)
            age = (now - last.astimezone(dt.timezone.utc)).total_seconds()
            if age < minutes * 60:
                return False
        except Exception:
            pass

    data[key] = now.replace(microsecond=0).isoformat()
    tmp = _SIGNAL_COOLDOWN_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_SIGNAL_COOLDOWN_PATH)
    return True


def should_notify_signal(signal: dict[str, Any]) -> tuple[bool, str]:
    from backend.notifier.preferences import read_preferences, selected_symbols

    prefs = read_preferences()
    if not prefs["enabled"] or not prefs["notify_signals"]:
        return False, "telegram signal notifications disabled"

    symbol = str(signal.get("symbol", "")).upper()
    sig_type = str(signal.get("signal_type", "")).upper()
    strength = int(signal.get("strength", 0) or 0)
    metadata = signal.get("metadata") or {}
    consensus_ratio = float(metadata.get("consensus_ratio", 0) or 0)

    symbols = selected_symbols(prefs)
    if symbols and symbol not in symbols:
        return False, "symbol filtered"
    if sig_type not in set(prefs["signal_types"]):
        return False, "signal type filtered"
    if strength < int(prefs["min_strength"]):
        return False, "signal strength filtered"
    if sig_type.startswith("STRONG") and consensus_ratio < float(prefs["min_consensus_ratio"]):
        return False, "consensus ratio filtered"
    if _in_quiet_hours(str(prefs.get("quiet_hours") or "")):
        return False, "quiet hours"

    key = f"{symbol}:{sig_type}"
    if not _cooldown_allowed(key, int(prefs["cooldown_minutes"])):
        return False, "cooldown"
    return True, ""


async def send_telegram(
    text: str,
    parse_mode: str = "Markdown",
    source: str | None = None,
) -> bool:
    """Ham metin gönder. Diğer fonksiyonlar bunu çağırır."""
    if not _configured():
        return False
    text = _with_source(text, source)
    try:
        import httpx

        token = getenv("TELEGRAM_BOT_TOKEN")
        chat_id = getenv("TELEGRAM_CHAT_ID")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            )
            if resp.status_code == 400 and parse_mode:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text},
                )
        if resp.status_code == 200:
            return True
        logger.warning(
            "telegram: API hatası %d — %s", resp.status_code, resp.text[:200]
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram: gönderim başarısız — %s", exc)
        return False


# ── Olay bildirimleri ────────────────────────────────────────────────────────

async def bildir_bot_basladi() -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_system"]:
        return False
    if not _lifecycle_allowed("bot_basladi"):
        logger.info("telegram: başlatıldı bildirimi 60 sn içinde tekrarlandığı için gönderilmedi")
        return False
    return await send_telegram(
        "🟢 *PiyasaPilot başlatıldı*\n"
        "Notifier ve Telegram listener çalışıyor. Sinyaller izleniyor.",
        source="Sistem bildirimi",
    )


async def bildir_bot_durdu() -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_system"]:
        return False
    if not _lifecycle_allowed("bot_durdu"):
        logger.info("telegram: durduruldu bildirimi 60 sn içinde tekrarlandığı için gönderilmedi")
        return False
    return await send_telegram(
        "🔴 *PiyasaPilot durduruldu*\n"
        "Notifier kapatıldı. Açık pozisyonlar korunuyor.",
        source="Sistem bildirimi",
    )


async def bildir_yeni_sinyal(signal: dict[str, Any]) -> bool:
    allowed, reason_filtered = should_notify_signal(signal)
    if not allowed:
        logger.info("telegram: sinyal filtrelendi — %s", reason_filtered)
        return False
    symbol = signal.get("symbol", "?")
    sig_type = signal.get("signal_type", "?")
    price = float(signal.get("price", 0))
    strategy = signal.get("strategy_id", "?")
    strength = int(signal.get("strength", 5))
    reason = signal.get("reason", "")
    stars = "⭐" * min(strength // 2, 5)
    emoji = "🟢" if "BUY" in sig_type else "🔴"
    return await send_telegram(
        f"{emoji} *Yeni Sinyal — {sig_type}*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📊 Strateji: `{strategy}`\n"
        f"💪 Güç: {strength}/10 {stars}\n"
        f"📝 {reason}",
        source="Sinyal bildirimi",
    )


async def bildir_alim(strategy_id: str, symbol: str, price: float,
                      quantity: float, tutar: float, reason: str) -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_trades"]:
        return False
    return await send_telegram(
        f"🛒 *Alım Gerçekleşti*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📦 Miktar: `{quantity:.4f}`\n"
        f"💵 Tutar: `{tutar:,.2f}₺`\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📝 {reason}",
        source="Sistem bildirimi",
    )


async def bildir_satim(strategy_id: str, symbol: str, price: float,
                       quantity: float, pnl: float, reason: str) -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_trades"]:
        return False
    emoji = "🟢" if pnl >= 0 else "🔴"
    isaret = "+" if pnl >= 0 else ""
    return await send_telegram(
        f"💸 *Satım Gerçekleşti*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📦 Miktar: `{quantity:.4f}`\n"
        f"{emoji} Kâr/Zarar: `{isaret}{pnl:,.2f}₺`\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📝 {reason}",
        source="Sistem bildirimi",
    )


async def bildir_cuzdan_donduruldu(strategy_id: str, daily_loss: float,
                                   initial_capital: float) -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_trades"]:
        return False
    oran = abs(daily_loss) / initial_capital * 100
    return await send_telegram(
        f"⛔ *Cüzdan Donduruldu*\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📉 Günlük zarar: `{daily_loss:,.2f}₺` (`{oran:.1f}%`)\n"
        f"ℹ️ Günlük zarar limiti aşıldı. Yeni işlem yapılmayacak.",
        source="Sistem bildirimi",
    )


async def bildir_hata(hata: str, baglam: str = "") -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_system"]:
        return False
    mesaj = f"⚠️ *Hata Oluştu*\n`{hata}`"
    if baglam:
        mesaj += f"\n📍 Bağlam: {baglam}"
    return await send_telegram(mesaj, source="Sistem bildirimi")


async def bildir_gunluk_ozet(wallets: list[dict], trades: list[dict]) -> bool:
    from backend.notifier.preferences import read_preferences

    if not read_preferences()["notify_daily_summary"]:
        return False
    satirlar = ["📊 *Günlük Paper Trading Özeti*\n"]
    for w in wallets:
        pnl = w["cash"] - w["initial_capital"]
        emoji = "🟢" if pnl >= 0 else "🔴"
        durum = "🔒 Donduruldu" if w["is_halted"] else "✅ Aktif"
        satirlar.append(
            f"*{w['strategy_id']}*: {durum}\n"
            f"  {emoji} Nakit: `{w['cash']:,.2f}₺` | PnL: `{pnl:+,.2f}₺`"
        )
    tamamlanan = [t for t in trades if t.get("closed_at")]
    kazananlar = [t for t in tamamlanan if (t.get("pnl") or 0) > 0]
    if tamamlanan:
        win_rate = len(kazananlar) / len(tamamlanan) * 100
        satirlar.append(
            f"\n📈 Kazanma Oranı: `{win_rate:.1f}%` "
            f"({len(kazananlar)}/{len(tamamlanan)} işlem)"
        )
    return await send_telegram("\n".join(satirlar), source="Sistem bildirimi")


async def test_baglantisi() -> bool:
    """Bağlantı testi — 'Telegram bağlantısı başarılı.' mesajı gönderir."""
    tamam = await send_telegram(
        "✅ *Telegram bağlantısı başarılı.*\n"
        "PiyasaPilot bildirim sistemi hazır.",
        source="Sistem bildirimi",
    )
    if tamam:
        logger.info("telegram: bağlantı testi başarılı")
    else:
        logger.error("telegram: bağlantı testi başarısız — .env dosyasını kontrol et")
    return tamam

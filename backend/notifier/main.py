"""Bildirim servisi ana döngüsü (Sprint 7).

/ws/signals WebSocket'ten STRONG sinyalleri dinler; her sinyal için
Telegram + macOS notification gönderir. Günlük 09:00'da özet gönderir.
docker-compose'da ayrı `notifier` container olarak çalışır.

Gerekli .env değişkenleri:
  TELEGRAM_BOT_TOKEN   — BotFather'dan alınan token
  TELEGRAM_CHAT_ID     — Hedef chat/kullanıcı ID
  NOTIFY_API_URL       — Backend adresi (varsayılan: http://localhost:8000)
  NOTIFY_POLL_INTERVAL — Yeniden bağlanma bekleme süresi (sn, varsayılan: 30)
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# ── Durumu takip et (API endpoint için) ─────────────────────────────────────
_durum: dict = {
    "aktif": False,
    "son_bildirim": None,
    "son_hata": None,
    "toplam_bildirim": 0,
    "son_sinyaller": [],  # Son 20 sinyal — /son komutu için
}

_MAX_RECENT = 20


def get_notifier_status() -> dict:
    d = dict(_durum)
    d["son_sinyaller"] = list(_durum["son_sinyaller"])
    return d


def _publish_status() -> None:
    try:
        from backend.notifier.service_status import write_notifier_status

        write_notifier_status(_durum)
    except Exception as exc:  # noqa: BLE001
        logger.debug("notifier: durum yazılamadı — %s", exc)


def _kaydet_sinyal(msg: dict) -> None:
    """Gelen sinyali son_sinyaller listesine ekle (max 20)."""
    _durum["son_sinyaller"].insert(0, msg)
    if len(_durum["son_sinyaller"]) > _MAX_RECENT:
        _durum["son_sinyaller"] = _durum["son_sinyaller"][:_MAX_RECENT]


# ── macOS native bildirim ────────────────────────────────────────────────────
def macos_notify(title: str, message: str) -> None:
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            [
                "osascript", "-e",
                f'display notification "{message}" with title "{title}" sound name "Glass"',
            ],
            check=False,
            timeout=5,
        )
    except Exception:  # noqa: BLE001
        pass


# ── Ana bildirim döngüsü ─────────────────────────────────────────────────────
async def notification_loop() -> None:
    """STRONG sinyalleri dinle ve bildir."""
    from backend.notifier.preferences import read_preferences, selected_symbols
    from backend.notifier.telegram import bildir_hata, bildir_yeni_sinyal

    logger.info("notifier: başlatılıyor...")
    _durum["aktif"] = True
    _publish_status()

    from backend.config import getenv

    poll_interval = int(getenv("NOTIFY_POLL_INTERVAL", "30"))
    api_url = getenv("NOTIFY_API_URL", "http://localhost:8000")
    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")

    while True:
        try:
            import websockets

            prefs = read_preferences()
            query: list[str] = []
            signal_types = ",".join(prefs["signal_types"])
            if signal_types:
                query.append(f"types={signal_types}")
            symbols = ",".join(selected_symbols(prefs))
            if symbols:
                query.append(f"symbols={symbols}")
            ws_path = "/ws/signals" + (f"?{'&'.join(query)}" if query else "")
            logger.info("notifier: %s%s adresine bağlanılıyor...", ws_url, ws_path)
            async with websockets.connect(
                f"{ws_url}{ws_path}",
                close_timeout=5,
                ping_interval=30,
            ) as ws:
                logger.info("notifier: bağlantı kuruldu, sinyaller dinleniyor")
                async for msg_raw in ws:
                    import json
                    try:
                        msg = json.loads(msg_raw)
                    except json.JSONDecodeError:
                        continue

                    if msg.get("type") != "signal":
                        continue

                    symbol = msg.get("symbol", "?")
                    sig_type = msg.get("signal_type", "?")

                    # Son sinyaller listesine ekle
                    _kaydet_sinyal(msg)

                    # Telegram (ikinci katman filtre bildir_yeni_sinyal içinde)
                    sent = await bildir_yeni_sinyal(msg)

                    # macOS
                    if sent:
                        macos_notify("PiyasaPilot", f"{sig_type} — {symbol}")

                    if sent:
                        now = dt.datetime.now(dt.UTC).isoformat()
                        _durum["son_bildirim"] = now
                        _durum["toplam_bildirim"] += 1
                        _publish_status()
                        logger.info("notifier: bildirim gönderildi — %s %s", sig_type, symbol)

        except Exception as exc:  # noqa: BLE001
            hata_msg = f"{type(exc).__name__}: {exc}"
            _durum["son_hata"] = hata_msg
            _publish_status()
            logger.warning("notifier: bağlantı hatası — %s", hata_msg)
            try:
                await bildir_hata(hata_msg, "notification_loop")
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(poll_interval)
            _publish_status()


async def daily_summary_loop() -> None:
    """Her gün 09:00'da günlük paper trading özeti gönder."""
    from backend.notifier.telegram import bildir_gunluk_ozet

    while True:
        now = dt.datetime.now()
        # Bir sonraki 09:00'a kadar bekle
        hedef = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= hedef:
            hedef += dt.timedelta(days=1)
        bekle = (hedef - now).total_seconds()
        logger.info("notifier: günlük özet %s'de gönderilecek (%.0f sn)", hedef, bekle)
        await asyncio.sleep(bekle)

        try:
            import httpx

            from backend.config import getenv

            api_url = getenv("NOTIFY_API_URL", "http://localhost:8000")
            async with httpx.AsyncClient(timeout=10) as client:
                wallets_resp = await client.get(f"{api_url}/api/paper/wallets")
                trades_resp = await client.get(f"{api_url}/api/paper/trades?limit=50")
            wallets = wallets_resp.json().get("wallets", [])
            trades = trades_resp.json().get("trades", [])
            await bildir_gunluk_ozet(wallets, trades)
            _publish_status()
            logger.info("notifier: günlük özet gönderildi")
        except Exception as exc:  # noqa: BLE001
            logger.warning("notifier: günlük özet hatası — %s", exc)


async def status_heartbeat_loop() -> None:
    """Ayrı API süreci için notifier canlılık heartbeat'i yaz."""
    while True:
        _publish_status()
        await asyncio.sleep(30)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    # httpx/httpcore INFO logları Telegram URL'sini token ile yazabilir.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    async def run() -> None:
        from backend.notifier.telegram import bildir_bot_basladi, bildir_bot_durdu
        from backend.notifier.telegram_listener import listener_loop

        await bildir_bot_basladi()
        try:
            await asyncio.gather(
                notification_loop(),
                daily_summary_loop(),
                listener_loop(),
                status_heartbeat_loop(),
            )
        finally:
            _durum["aktif"] = False
            _publish_status()
            try:
                await asyncio.shield(bildir_bot_durdu())
            except Exception as exc:  # noqa: BLE001
                logger.debug("notifier: durduruldu bildirimi gönderilemedi — %s", exc)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("notifier: kullanıcı tarafından durduruldu")


if __name__ == "__main__":
    main()

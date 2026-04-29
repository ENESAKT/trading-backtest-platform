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
import os
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
    from backend.notifier.telegram import bildir_yeni_sinyal, bildir_hata

    logger.info("notifier: başlatılıyor...")
    _durum["aktif"] = True

    poll_interval = int(os.getenv("NOTIFY_POLL_INTERVAL", "30"))
    api_url = os.getenv("NOTIFY_API_URL", "http://localhost:8000")
    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")

    while True:
        try:
            import websockets

            logger.info("notifier: %s/ws/signals adresine bağlanılıyor...", ws_url)
            async with websockets.connect(
                f"{ws_url}/ws/signals?types=STRONG_BUY,STRONG_SELL",
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

                    # Telegram
                    await bildir_yeni_sinyal(msg)

                    # macOS
                    macos_notify("PiyasaPilot", f"{sig_type} — {symbol}")

                    now = dt.datetime.now(dt.UTC).isoformat()
                    _durum["son_bildirim"] = now
                    _durum["toplam_bildirim"] += 1
                    logger.info("notifier: bildirim gönderildi — %s %s", sig_type, symbol)

        except Exception as exc:  # noqa: BLE001
            hata_msg = f"{type(exc).__name__}: {exc}"
            _durum["son_hata"] = hata_msg
            logger.warning("notifier: bağlantı hatası — %s", hata_msg)
            try:
                await bildir_hata(hata_msg, "notification_loop")
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(poll_interval)


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
            api_url = os.getenv("NOTIFY_API_URL", "http://localhost:8000")
            async with httpx.AsyncClient(timeout=10) as client:
                wallets_resp = await client.get(f"{api_url}/api/paper/wallets")
                trades_resp = await client.get(f"{api_url}/api/paper/trades?limit=50")
            wallets = wallets_resp.json().get("wallets", [])
            trades = trades_resp.json().get("trades", [])
            await bildir_gunluk_ozet(wallets, trades)
            logger.info("notifier: günlük özet gönderildi")
        except Exception as exc:  # noqa: BLE001
            logger.warning("notifier: günlük özet hatası — %s", exc)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    async def run() -> None:
        from backend.notifier.telegram_listener import listener_loop

        await asyncio.gather(
            notification_loop(),
            daily_summary_loop(),
            listener_loop(),
        )

    asyncio.run(run())


if __name__ == "__main__":
    main()

"""Bildirim servisi ana döngüsü (Sprint 7).

Signal bus'tan sinyal alır → Telegram/Email/macOS notification gönderir.
docker-compose'da ayrı container olarak çalışır.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

# macOS native bildirim (sadece lokal modda)
def macos_notify(title: str, message: str) -> None:
    """macOS AppleScript notification."""
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


async def notification_loop() -> None:
    """Ana bildirim döngüsü — signal API'yi poll'lar ve STRONG sinyallerde bildirim gönderir."""
    from backend.notifier.telegram import send_telegram, format_signal

    logger.info("notifier: başlatılıyor...")

    poll_interval = int(os.getenv("NOTIFY_POLL_INTERVAL", "30"))
    api_url = os.getenv("NOTIFY_API_URL", "http://localhost:8000")

    last_signal_ts = ""

    while True:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                # Son sinyalleri çek
                resp = await client.get(f"{api_url}/api/health")
                if resp.status_code != 200:
                    await asyncio.sleep(poll_interval)
                    continue

            # STRONG sinyaller için WS'ye bağlan
            import websockets

            try:
                async with websockets.connect(
                    f"ws://localhost:8000/ws/signals?types=STRONG_BUY,STRONG_SELL",
                    close_timeout=5,
                ) as ws:
                    async for msg_raw in ws:
                        import json
                        msg = json.loads(msg_raw)

                        if msg.get("type") == "signal":
                            ts = msg.get("ts", "")
                            if ts <= last_signal_ts:
                                continue
                            last_signal_ts = ts

                            text = format_signal(msg)

                            # Telegram
                            await send_telegram(text)

                            # macOS notification
                            sym = msg.get("symbol", "?")
                            sig = msg.get("signal_type", "?")
                            macos_notify("PiyasaPilot", f"{sig} — {sym}")

                            logger.info("notifier: STRONG sinyal bildirimi gönderildi — %s %s", sig, sym)

            except Exception as exc:  # noqa: BLE001
                logger.warning("notifier: WS bağlantı hatası — %s", exc)
                await asyncio.sleep(poll_interval)

        except Exception as exc:  # noqa: BLE001
            logger.warning("notifier: döngü hatası — %s", exc)
            await asyncio.sleep(poll_interval)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    asyncio.run(notification_loop())


if __name__ == "__main__":
    main()

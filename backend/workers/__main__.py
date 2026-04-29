"""Standalone worker modu — yalnızca SQLite cache doldurur.

Bu entrypoint ``Dockerfile.workers`` tarafından kullanılır. FastAPI sunucusu
veya WS bus olmadan sadece worker daemon'larını çalıştırır; her bar geldiğinde
``OHLCVCache.upsert_bars`` ile yazar.

Çalıştırma:
    python -m backend.workers

Not: Gerçek zamanlı /ws/quotes ve /ws/signals yayını için worker'ların API
süreci içinde çalışması gerekir. Bu mod yalnızca önbellek ön-doldurmak veya
api servisinden bağımsız cache güncellemesi için tasarlanmıştır.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from backend.data.cache import OHLCVCache
from backend.data.symbols import (
    BIST_STOCKS,
    CRYPTO_WS_SYMBOLS,
    DEFAULT_INTERVAL,
    YAHOO_INDEX_FX_COMMODITY,
)
from backend.workers import WorkerSupervisor
from backend.workers.binance_ws import BinanceKlineWorker
from backend.workers.bist_poller import BistStockPoller
from backend.workers.yahoo_poller import YahooPoller
from quant_engine.data.live_feed import LiveDataService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("workers.main")


async def run() -> None:
    cache = OHLCVCache()
    data_service = LiveDataService()

    supervisor = WorkerSupervisor(
        [
            BinanceKlineWorker(
                cache=cache,
                symbols=CRYPTO_WS_SYMBOLS,
                interval=DEFAULT_INTERVAL,
            ),
            YahooPoller(
                cache=cache,
                data_service=data_service,
                symbols=YAHOO_INDEX_FX_COMMODITY,
                interval=DEFAULT_INTERVAL,
            ),
            BistStockPoller(
                cache=cache,
                data_service=data_service,
                symbols=BIST_STOCKS,
                interval=DEFAULT_INTERVAL,
            ),
        ]
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(*_: object) -> None:
        logger.info("Kapatma sinyali alındı, worker'lar durduruluyor…")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    logger.info("Worker'lar başlatılıyor (%d adet)…", len(supervisor.workers))
    await supervisor.start_all()

    try:
        await stop_event.wait()
    finally:
        await supervisor.stop_all()
        logger.info("Tüm worker'lar durduruldu.")


if __name__ == "__main__":
    asyncio.run(run())

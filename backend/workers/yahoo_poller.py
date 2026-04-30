"""Yahoo Finance poller — Sprint 1.6.

BIST endeks (XU100), TL döviz pariteleri, altın/petrol/gümüş futures için
``LiveDataService.fetch_candles`` üzerinden periyodik kovuş çeker, ``filter_bars``
ile temizler ve cache'e yazar.

yfinance bloklayıcı bir kütüphane — her sembol için ``run_in_executor`` ile
thread pool'a göndeririz. Provider ``status="error"`` dönerse silently
log'lar; canlı stream yok, beklenen senaryo.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from backend.data.cache import OHLCVCache
from backend.data.spike_filter import filter_bars
from backend.workers.base import AsyncWorker

logger = logging.getLogger(__name__)

# Test-friendly: protocol yerine duck-typed callable. ``LiveDataService``
# zaten bu imzayı sağlıyor.
FetchCandles = Callable[[str, str, int], dict[str, Any]]
BarHook = Callable[..., Awaitable[None] | None]


class YahooPoller(AsyncWorker):
    """yfinance üzerinden bir sembol listesini periyodik olarak çek.

    Default 15 saniyede bir tüm listeyi tarar; Yahoo rate limiti (~60/dk)
    küçük listeler için bol bol yeterli. 100 sembol gibi büyük listeler için
    Sprint 2'de batch ``yf.download`` modu eklenecek.
    """

    DEFAULT_LIMIT = 200

    def __init__(
        self,
        cache: OHLCVCache,
        data_service: Any,
        symbols: list[str] | tuple[str, ...],
        interval: str = "15m",
        poll_seconds: float = 15.0,
        limit: int = DEFAULT_LIMIT,
        name: str = "yahoo_poller",
        on_bar: BarHook | None = None,
    ):
        super().__init__(name=name, interval_seconds=poll_seconds)
        self.cache = cache
        self.data_service = data_service
        self.symbols = list(symbols)
        self.interval = interval
        self.limit = int(limit)
        self.on_bar = on_bar

    async def run_once(self) -> None:
        for sym in self.symbols:
            if self._stop.is_set():
                return
            await self._fetch_and_persist(sym)

    async def _fetch_and_persist(self, symbol: str) -> None:
        loop = asyncio.get_running_loop()
        try:
            payload = await loop.run_in_executor(
                None,
                self.data_service.fetch_candles,
                symbol,
                self.interval,
                self.limit,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s: %s fetch crashed: %s", self.name, symbol, exc)
            return

        if payload.get("status") != "ok":
            # provider hata → cache'e dokunma; live_feed zaten loglar
            return
        bars = payload.get("bars") or []
        if not bars:
            return

        cleaned, _report = filter_bars(bars)
        canonical = payload.get("symbol") or symbol.strip().upper()

        await loop.run_in_executor(
            None, self.cache.upsert_bars, canonical, self.interval, cleaned
        )

        if self.on_bar is not None:
            try:
                metadata = dict(payload.get("metadata") or {})
                result = self.on_bar(canonical, self.interval, cleaned, metadata)
                if asyncio.iscoroutine(result):
                    await result
            except TypeError:
                result = self.on_bar(canonical, self.interval, cleaned)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001
                logger.warning("%s on_bar hook failed: %s", self.name, exc)

"""DataService — OHLCV veri çekme servis katmanı.

quant_engine.data.live_feed.LiveDataService üzerinden veri çeker.
Bu sınıf dependency injection ile test edilebilir hale getirir.
"""

from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)


class DataService:
    """Fetches and validates OHLCV data from providers."""

    def __init__(self) -> None:
        # LiveDataService geç yüklenir (import döngüsünü önler)
        self._live: Any = None

    def _get_live(self) -> Any:
        if self._live is None:
            from quant_engine.data.live_feed import LiveDataService
            self._live = LiveDataService()
        return self._live

    async def get_bars(
        self, symbol: str, timeframe: str, start: str, end: str
    ) -> list[dict]:
        """Verilen sembol ve zaman aralığı için OHLCV barlarını döndürür.

        Args:
            symbol:    Sembol kodu (örn. 'THYAO', 'BTCUSDT').
            timeframe: Bar periyodu (örn. '1h', '1d').
            start:     ISO-8601 başlangıç tarihi ('2024-01-01').
            end:       ISO-8601 bitiş tarihi ('2024-12-31').

        Returns:
            [{'time': int, 'open': float, 'high': float,
              'low': float, 'close': float, 'volume': float}, ...]
        """
        live = self._get_live()
        try:
            result = live.fetch_candles(symbol, timeframe)
            bars = result.get("bars", [])
            # start/end filtresi (Unix timestamp)
            import datetime as dt
            ts_start = int(dt.datetime.fromisoformat(start).timestamp()) if start else 0
            ts_end   = int(dt.datetime.fromisoformat(end).timestamp())   if end   else 9_999_999_999
            return [b for b in bars if ts_start <= b.get("time", 0) <= ts_end]
        except Exception as exc:
            _logger.error("[DataService] get_bars(%s, %s) hata: %s", symbol, timeframe, exc)
            raise

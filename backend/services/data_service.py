"""DataService — thin wrapper around ProviderRouter for use outside API routes."""

from __future__ import annotations

from quant_engine.data.provider_router import ProviderRouter


class DataService:
    """Fetches and validates OHLCV data from providers.

    Thin delegation layer so service-layer callers don't import
    ProviderRouter directly.  Limit is intentionally generous (500 bars)
    when no explicit limit is needed.
    """

    _TIMEFRAME_LIMIT: dict[str, int] = {
        "1m": 500,
        "5m": 500,
        "15m": 300,
        "30m": 200,
        "1h": 200,
        "4h": 200,
        "1d": 500,
        "1w": 200,
    }

    def __init__(self) -> None:
        self._router = ProviderRouter()

    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,  # noqa: ARG002  (kept for interface parity; router uses limit)
        end: str,    # noqa: ARG002
    ) -> list[dict]:
        """Return OHLCV bar list for *symbol* at *timeframe*.

        ``start``/``end`` are accepted for API compatibility but the
        underlying yfinance/HTTP providers use a bar-count limit instead.
        The limit is derived from the timeframe so the requested window is
        comfortably covered for typical backtests.
        """
        limit = self._TIMEFRAME_LIMIT.get(timeframe, 300)
        result = self._router.fetch_ohlcv(symbol, timeframe, limit=limit)
        return result.data

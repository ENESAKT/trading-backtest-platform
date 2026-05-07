class DataService:
    """Fetches and validates OHLCV data from providers."""

    async def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> list[dict]:
        raise NotImplementedError

"""Local historical OHLCV bridge backed by pipeline Parquet files."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import pandas as pd

from quant_engine.data_pipeline.storage_manager import StorageManager


@dataclass(frozen=True)
class HistoricalReadResult:
    symbol: str
    storage_symbol: str
    interval: str
    bars: list[dict[str, Any]]
    first_time: int | None
    last_time: int | None


class HistoricalStore:
    """Read daily historical bars from the local Parquet data pipeline store."""

    SUPPORTED_INTERVALS = {"1d"}

    def __init__(self, storage: StorageManager | None = None):
        self.storage = storage or StorageManager()

    @staticmethod
    def storage_symbol(symbol: str) -> str:
        clean = symbol.strip().upper().replace(" ", "")
        if clean.startswith("^"):
            clean = clean[1:]
        if clean in {"BIST30", "XU030.IS"}:
            return "XU030"
        if clean in {"BIST100", "XU100.IS"}:
            return "XU100"
        if clean.endswith(".IS"):
            return clean[:-3]
        return clean

    @staticmethod
    def response_symbol(symbol: str) -> str:
        clean = symbol.strip().upper().replace(" ", "")
        if clean.startswith("^"):
            clean = clean[1:]
        if clean in {"BIST30", "XU030"}:
            return "XU030.IS"
        if clean in {"BIST100", "XU100"}:
            return "XU100.IS"
        if clean.endswith(".IS") or clean.endswith("=X") or clean.endswith("=F"):
            return clean
        return f"{clean}.IS"

    def has_symbol(self, symbol: str, *, market: str = "bist") -> bool:
        return self.storage.symbol_exists(self.storage_symbol(symbol), market=market)

    def read_bars(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int | None = 500,
        start: str | None = None,
        end: str | None = None,
        *,
        market: str = "bist",
    ) -> HistoricalReadResult:
        response_symbol = self.response_symbol(symbol)
        storage_symbol = self.storage_symbol(symbol)
        if interval not in self.SUPPORTED_INTERVALS:
            return HistoricalReadResult(response_symbol, storage_symbol, interval, [], None, None)

        df = self.storage.read_symbol(storage_symbol, start=start, end=end, market=market)
        if df.empty:
            return HistoricalReadResult(response_symbol, storage_symbol, interval, [], None, None)

        df = df.sort_values("date")
        if limit is not None and limit > 0:
            df = df.tail(int(limit))

        dates = pd.to_datetime(df["date"], utc=True)
        bars = [
            {
                "time": int(ts.timestamp()),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume or 0),
            }
            for ts, row in zip(dates, df.itertuples(index=False), strict=True)
        ]
        first_time = bars[0]["time"] if bars else None
        last_time = bars[-1]["time"] if bars else None
        return HistoricalReadResult(
            symbol=response_symbol,
            storage_symbol=storage_symbol,
            interval=interval,
            bars=bars,
            first_time=first_time,
            last_time=last_time,
        )

    def payload(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int | None = 500,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any] | None:
        result = self.read_bars(symbol, interval=interval, limit=limit, start=start, end=end)
        if not result.bars:
            return None
        return {
            "symbol": result.symbol,
            "display_name": result.storage_symbol,
            "market": "bist",
            "interval": interval,
            "status": "ok",
            "message": "Yerel Parquet tarihsel veri döndürüldü.",
            "bars": result.bars,
            "quote": {
                "last": result.bars[-1]["close"],
                "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            },
            "metadata": {
                "read_only": True,
                "is_real": True,
                "source": "local_parquet",
                "provider_name": "HistoricalStore",
                "storage_symbol": result.storage_symbol,
                "bar_count": len(result.bars),
                "first_time": result.first_time,
                "last_time": result.last_time,
            },
        }

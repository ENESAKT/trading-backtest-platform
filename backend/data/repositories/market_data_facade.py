"""Sync market data facade for Redis -> ClickHouse candle reads.

The FastAPI gateway is mostly synchronous today, so this facade keeps the DB
integration small and optional. If Redis or ClickHouse is unavailable, callers
get an empty result and the legacy provider/SQLite path continues.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import clickhouse_connect
import redis

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CandleReadResult:
    bars: list[dict[str, Any]]
    source: str


def _market_for_symbol(symbol: str) -> tuple[str, str]:
    normalized = symbol.strip().upper()
    if normalized.endswith(".IS"):
        return "BIST", "stock"
    if normalized.endswith("USDT") or normalized.endswith("USD"):
        return "CRYPTO", "spot"
    if normalized.startswith("F_") or normalized.startswith("VIOP:"):
        return "VIOP", "contract"
    return "GLOBAL", "unknown"


def _bar_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000 if value > 9_999_999_999 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _to_api_bar(row: dict[str, Any]) -> dict[str, Any]:
    ts = row["ts"]
    if isinstance(ts, datetime):
        millis = int(ts.timestamp() * 1000)
    else:
        millis = int(_bar_time(ts).timestamp() * 1000)
    return {
        "time": millis,
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": float(row.get("volume") or 0),
    }


class MarketDataFacade:
    """Optional production data facade for hot cache and OHLCV store."""

    def __init__(self) -> None:
        self._redis = None
        self._clickhouse = None

    @classmethod
    def from_env(cls) -> "MarketDataFacade":
        return cls()

    def _redis_client(self):
        if self._redis is None:
            self._redis = redis.Redis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
        return self._redis

    def _clickhouse_client(self):
        if self._clickhouse is None:
            raw_url = os.environ.get("CLICKHOUSE_URL", "http://localhost:8123/market_data")
            parsed = urlparse(raw_url)
            self._clickhouse = clickhouse_connect.get_client(
                host=parsed.hostname or "localhost",
                port=parsed.port or 8123,
                username=os.environ.get("CLICKHOUSE_USER", "default"),
                password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
                database=(parsed.path or "/market_data").strip("/") or "market_data",
                connect_timeout=1,
                send_receive_timeout=2,
            )
        return self._clickhouse

    def _cache_key(self, symbol: str, interval: str, limit: int) -> str:
        return f"cache:candles:{symbol.strip().upper()}:{interval}:{limit}"

    def read_candles(self, symbol: str, interval: str, limit: int) -> CandleReadResult | None:
        canonical = symbol.strip().upper()
        safe_limit = max(1, min(int(limit or 500), 5000))
        key = self._cache_key(canonical, interval, safe_limit)

        try:
            cached = self._redis_client().get(key)
            if cached:
                bars = json.loads(cached)
                if bars:
                    return CandleReadResult(bars=bars, source="redis")
        except Exception as exc:  # noqa: BLE001
            _logger.debug("[market-data] Redis read skipped: %s", exc)

        market, _instrument_type = _market_for_symbol(canonical)
        try:
            rows = self._clickhouse_client().query(
                """
                SELECT ts, open, high, low, close, volume
                FROM market_bars
                WHERE market = {market:String}
                  AND symbol = {symbol:String}
                  AND timeframe = {timeframe:String}
                ORDER BY ts DESC
                LIMIT {limit:UInt32}
                """,
                parameters={
                    "market": market,
                    "symbol": canonical,
                    "timeframe": interval,
                    "limit": safe_limit,
                },
            )
            bars = [
                _to_api_bar(dict(zip(rows.column_names, row, strict=True)))
                for row in reversed(rows.result_rows)
            ]
            if bars:
                self.write_redis(canonical, interval, safe_limit, bars)
                return CandleReadResult(bars=bars, source="clickhouse")
        except Exception as exc:  # noqa: BLE001
            _logger.debug("[market-data] ClickHouse read skipped: %s", exc)

        return None

    def write_candles(
        self,
        symbol: str,
        interval: str,
        bars: list[dict[str, Any]],
        *,
        source: str,
        limit: int,
    ) -> None:
        if not bars:
            return
        canonical = symbol.strip().upper()
        self.write_redis(canonical, interval, limit, bars)
        market, instrument_type = _market_for_symbol(canonical)
        rows = []
        for bar in bars:
            try:
                rows.append([
                    market,
                    canonical,
                    instrument_type,
                    interval,
                    _bar_time(bar["time"]),
                    float(bar["open"]),
                    float(bar["high"]),
                    float(bar["low"]),
                    float(bar["close"]),
                    float(bar.get("volume") or 0),
                    source,
                    interval,
                    0,
                    "ok",
                    "",
                    datetime.now(timezone.utc),
                ])
            except Exception:
                continue
        if not rows:
            return
        try:
            self._clickhouse_client().insert(
                "market_bars",
                rows,
                column_names=[
                    "market",
                    "symbol",
                    "instrument_type",
                    "timeframe",
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "source",
                    "source_timeframe",
                    "is_derived",
                    "quality_status",
                    "ingest_job_id",
                    "ingested_at",
                ],
            )
        except Exception as exc:  # noqa: BLE001
            _logger.debug("[market-data] ClickHouse write skipped: %s", exc)

    def write_redis(
        self,
        symbol: str,
        interval: str,
        limit: int,
        bars: list[dict[str, Any]],
        ttl_seconds: int = 60,
    ) -> None:
        try:
            self._redis_client().set(
                self._cache_key(symbol, interval, max(1, min(int(limit or 500), 5000))),
                json.dumps(bars),
                ex=ttl_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.debug("[market-data] Redis write skipped: %s", exc)

"""
Quant Engine - Binance Spot public market data provider.

Bu provider yalnızca public market-data endpoint'lerini kullanır; API key,
hesap bilgisi veya emir yetkisi istemez. Kripto tarafında demo veri yerine
gerçek kline/OHLCV akışı gerektiğinde ücretsiz ve anahtarsız bir kaynak sağlar.
"""

from __future__ import annotations

import datetime as dt
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from quant_engine.core.protocols import (
    BarRequest,
    FetchResult,
    Market,
    ProviderCapabilities,
    Timeframe,
)
from quant_engine.data.providers.base import BaseProvider

BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_DATA_BASE_URL = "https://data-api.binance.vision"

_INTERVAL_MAP: dict[Timeframe, str] = {
    Timeframe.M1: "1m",
    Timeframe.M5: "5m",
    Timeframe.M15: "15m",
    Timeframe.M30: "30m",
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",
    Timeframe.D1: "1d",
    Timeframe.W1: "1w",
    Timeframe.MO1: "1M",
}

_SYMBOL_ALIASES: dict[str, str] = {
    "BTC": "BTCUSDT",
    "BTCUSD": "BTCUSDT",
    "BTCUSDT": "BTCUSDT",
    "BTC-USD": "BTCUSDT",
    "ETH": "ETHUSDT",
    "ETHUSD": "ETHUSDT",
    "ETHUSDT": "ETHUSDT",
    "ETH-USD": "ETHUSDT",
    "BNB": "BNBUSDT",
    "BNBUSD": "BNBUSDT",
    "BNBUSDT": "BNBUSDT",
    "SOL": "SOLUSDT",
    "SOLUSD": "SOLUSDT",
    "SOLUSDT": "SOLUSDT",
    "XRP": "XRPUSDT",
    "XRPUSD": "XRPUSDT",
    "XRPUSDT": "XRPUSDT",
}


def _to_binance_symbol(symbol: str) -> str:
    """Kullanıcı sembolünü Binance spot sembolüne çevir."""
    clean = symbol.upper().strip().replace("/", "").replace(" ", "")
    if clean in _SYMBOL_ALIASES:
        return _SYMBOL_ALIASES[clean]
    if clean.endswith("USD") and not clean.endswith("USDT"):
        return f"{clean[:-3]}USDT"
    return clean


def _to_binance_interval(timeframe: Timeframe) -> str:
    """Core Timeframe değerini Binance interval değerine çevir."""
    return _INTERVAL_MAP.get(timeframe, "1d")


def _date_to_millis(value: dt.date | None) -> int | None:
    if value is None:
        return None
    timestamp = dt.datetime.combine(value, dt.time.min, tzinfo=dt.UTC)
    return int(timestamp.timestamp() * 1000)


def _parse_klines(payload: list[list], symbol: str) -> pd.DataFrame:
    """Binance kline payload'unu standart OHLCV şemasına çevir."""
    rows = []
    for item in payload:
        rows.append(
            {
                "date": pd.to_datetime(int(item[0]), unit="ms", utc=True).tz_localize(None),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "symbol": symbol,
            }
        )
    return pd.DataFrame(rows)


class BinanceProvider(BaseProvider):
    """Binance Spot public kline provider."""

    def __init__(
        self,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 15.0,
        base_url: str = BINANCE_DATA_BASE_URL,
    ):
        super().__init__(
            retry_count=retry_count,
            retry_delay=retry_delay,
            timeout=timeout,
        )
        self.base_url = base_url.rstrip("/")

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name="binance",
            supported_markets=[Market.CRYPTO],
            supported_timeframes=list(_INTERVAL_MAP),
            supports_intraday=True,
            supports_live=False,
            max_history_days=None,
            rate_limit_per_minute=1200,
        )

    def _fetch_bars_impl(self, request: BarRequest) -> FetchResult:
        symbol = _to_binance_symbol(request.symbol)
        interval = _to_binance_interval(request.timeframe)
        start_ms = _date_to_millis(request.start)
        end_ms = _date_to_millis(request.end or dt.date.today() + dt.timedelta(days=1))

        all_rows: list[list] = []
        next_start = start_ms
        # Binance tek çağrıda en fazla 1000 kline döndürür; uzun geçmiş için sayfalıyoruz.
        for _ in range(20):
            params: dict[str, str | int] = {
                "symbol": symbol,
                "interval": interval,
                "limit": 1000,
            }
            if next_start is not None:
                params["startTime"] = next_start
            if end_ms is not None:
                params["endTime"] = end_ms
            url = f"{self.base_url}/api/v3/klines?{urlencode(params)}"
            req = Request(url, headers={"User-Agent": "QuantEngine/0.1"})
            with urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if not payload:
                break
            all_rows.extend(payload)
            last_open_time = int(payload[-1][0])
            next_start = last_open_time + 1
            if len(payload) < 1000 or (end_ms is not None and next_start >= end_ms):
                break

        if not all_rows:
            return FetchResult(
                symbol=symbol,
                data=pd.DataFrame(),
                source="binance",
                errors=[f"{symbol} için Binance kline verisi bulunamadı."],
            )

        df = _parse_klines(all_rows, symbol)
        df = df.drop_duplicates(subset=["date", "symbol"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        return FetchResult(symbol=symbol, data=df, source="binance")

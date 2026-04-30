"""Binance Spot public REST tabanlı kripto veri sağlayıcı."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from quant_engine.data.market_data import (
    MarketDataHealth,
    MarketDataProviderType,
    MarketDataResult,
    MarketDataStatus,
    utc_iso,
)

BINANCE_DATA_BASE_URL = "https://data-api.binance.vision"
BINANCE_REST_BASE_URL = "https://api.binance.com"


class CryptoMarketDataProvider:
    name = "binance_rest"
    source = "Binance Spot Public REST"

    _INTERVALS = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.last_success_at: str | None = None
        self.last_error: str | None = None

    @staticmethod
    def _source_symbol(symbol: str) -> str:
        clean = symbol.upper().strip().replace("/", "").replace("-", "")
        if clean.endswith("USD") and not clean.endswith("USDT"):
            return f"{clean[:-3]}USDT"
        return clean

    def _request_klines(
        self,
        base_url: str,
        symbol: str,
        interval: str,
        limit: int,
    ) -> list[list[Any]]:
        params = urlencode({
            "symbol": symbol,
            "interval": interval,
            "limit": max(1, min(int(limit), 1000)),
        })
        req = Request(
            f"{base_url.rstrip('/')}/api/v3/klines?{params}",
            headers={"User-Agent": "PiyasaPilot/1.0"},
        )
        with urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> MarketDataResult:
        source_symbol = self._source_symbol(symbol)
        interval = self._INTERVALS.get(timeframe, "15m")
        timestamp = utc_iso()
        payload: list[list[Any]] | None = None
        errors: list[str] = []

        # WS reset veya public data endpoint erişim sorunu olduğunda REST ana
        # endpoint'e düş. İki kaynak da public market-data; emir yetkisi yok.
        for base_url in (BINANCE_DATA_BASE_URL, BINANCE_REST_BASE_URL):
            try:
                payload = self._request_klines(base_url, source_symbol, interval, limit)
                if payload:
                    break
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{type(exc).__name__}: {exc}")
                payload = None

        if not payload:
            self.last_error = "Binance public veri bulunamadı."
            if errors:
                self.last_error += f" Son hata: {errors[-1][:120]}"
            return MarketDataResult(
                symbol=source_symbol,
                market="crypto",
                timeframe=timeframe,
                data=[],
                source=self.source,
                is_real=False,
                status=MarketDataStatus.NO_DATA,
                timestamp=timestamp,
                error=self.last_error,
                provider_name=self.name,
                display_name=source_symbol,
            )

        bars = [
            {
                "time": int(row[0]) // 1000,
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in payload
        ]
        self.last_success_at = timestamp
        self.last_error = None
        return MarketDataResult(
            symbol=source_symbol,
            market="crypto",
            timeframe=timeframe,
            data=bars,
            source=self.source,
            is_real=True,
            status=MarketDataStatus.OK,
            timestamp=timestamp,
            provider_name=self.name,
            display_name=source_symbol,
        )

    def health(self) -> MarketDataHealth:
        return MarketDataHealth(
            provider_name=self.name,
            provider_type=MarketDataProviderType.CRYPTO,
            active=True,
            configured=True,
            is_real=True,
            supported_markets=["crypto"],
            last_success_at=self.last_success_at,
            last_error=self.last_error,
            source=self.source,
        )

from __future__ import annotations

import pandas as pd

from quant_engine.data.market_data import MarketDataStatus
from quant_engine.data.provider_router import ProviderRouter
from quant_engine.data.providers.bist_provider import BistMarketDataProvider
from quant_engine.data.providers.crypto_provider import CryptoMarketDataProvider
from quant_engine.data.providers.viop_provider import ViopMarketDataProvider


def test_provider_router_routes_symbols():
    router = ProviderRouter()

    assert router.provider_for_symbol("THYAO").name == "bist_yfinance"
    assert router.provider_for_symbol("PETKM.IS").name == "bist_yfinance"
    assert router.provider_for_symbol("BTCUSDT").name == "binance_rest"
    assert router.provider_for_symbol("F_XU0300426").name == "viop_not_configured"


def test_bist_provider_returns_ok_with_yfinance_data(monkeypatch):
    provider = BistMarketDataProvider()
    frame = pd.DataFrame({
        "Datetime": pd.to_datetime(["2026-04-29T09:00:00Z", "2026-04-29T09:15:00Z"]),
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.5, 102.5],
        "Volume": [1000, 1100],
    })

    monkeypatch.setattr(provider, "_load_history", lambda *_args: frame)

    result = provider.fetch_ohlcv("THYAO", "15m", 20)
    assert result.status == MarketDataStatus.OK
    assert result.is_real is False
    assert result.symbol == "THYAO.IS"
    assert result.data[-1]["close"] == 102.5
    assert provider.health().is_real is False


def test_bist_provider_prefers_configured_http_feed(monkeypatch):
    provider = BistMarketDataProvider()
    monkeypatch.setenv("BIST_HTTP_URL_TEMPLATE", "https://data.example/{symbol}")
    monkeypatch.setattr(
        provider,
        "_fetch_configured_http",
        lambda *_args: [
            {
                "time": 1_700_000_000,
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "volume": 1000.0,
            }
        ],
    )

    result = provider.fetch_ohlcv("THYAO", "15m", 20)

    assert result.status == MarketDataStatus.OK
    assert result.is_real is True
    assert result.provider_name == "bist_http"
    assert result.source == "Configured BIST HTTP feed"
    assert result.data[0]["close"] == 10.5
    assert provider.health().is_real is True


def test_bist_provider_returns_no_data_without_rows(monkeypatch):
    provider = BistMarketDataProvider()
    monkeypatch.setattr(provider, "_load_history", lambda *_args: pd.DataFrame())

    result = provider.fetch_ohlcv("ASELS", "15m", 20)
    assert result.status == MarketDataStatus.NO_DATA
    assert result.is_real is False
    assert result.data == []


def test_viop_provider_is_not_configured():
    provider = ViopMarketDataProvider()
    result = provider.fetch_ohlcv("F_XU0300426", "15m", 20)

    assert result.status == MarketDataStatus.NOT_CONFIGURED
    assert result.is_real is False
    assert "yapılandırılmadı" in result.error


def test_viop_provider_uses_configured_http_feed(monkeypatch):
    import quant_engine.data.providers.viop_provider as viop_module

    provider = ViopMarketDataProvider()
    monkeypatch.setenv("VIOP_HTTP_URL_TEMPLATE", "https://viop.example/{symbol}")
    monkeypatch.setattr(
        viop_module,
        "fetch_http_ohlcv",
        lambda *_args, **_kwargs: [
            {
                "time": 1_700_000_000,
                "open": 1000.0,
                "high": 1010.0,
                "low": 990.0,
                "close": 1005.0,
                "volume": 100.0,
            }
        ],
    )

    result = provider.fetch_ohlcv("F_XU0300426", "15m", 20)
    health = provider.health()

    assert result.status == MarketDataStatus.OK
    assert result.is_real is True
    assert result.provider_name == "viop_http"
    assert result.data[0]["close"] == 1005.0
    assert health.configured is True


def test_crypto_provider_falls_back_to_second_rest_endpoint(monkeypatch):
    provider = CryptoMarketDataProvider()
    calls: list[str] = []

    def fake_request(base_url, symbol, interval, limit):
        calls.append(base_url)
        if len(calls) == 1:
            raise OSError("geçici bağlantı hatası")
        return [[1_700_000_000_000, "1", "2", "0.5", "1.5", "10"]]

    monkeypatch.setattr(provider, "_request_klines", fake_request)

    result = provider.fetch_ohlcv("BTCUSDT", "15m", 20)
    assert len(calls) == 2
    assert result.status == MarketDataStatus.OK
    assert result.is_real is True
    assert result.data[0]["close"] == 1.5

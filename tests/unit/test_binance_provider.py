from __future__ import annotations

from quant_engine.core.protocols import Market, Timeframe
from quant_engine.data.providers.binance_provider import (
    BinanceProvider,
    _parse_klines,
    _to_binance_interval,
    _to_binance_symbol,
)


def test_binance_symbol_aliases_normalize_to_usdt_pairs():
    assert _to_binance_symbol("BTC") == "BTCUSDT"
    assert _to_binance_symbol("BTC-USD") == "BTCUSDT"
    assert _to_binance_symbol("ETH/USD") == "ETHUSDT"
    assert _to_binance_symbol("SOLUSD") == "SOLUSDT"


def test_binance_interval_mapping_uses_core_timeframes():
    assert _to_binance_interval(Timeframe.M1) == "1m"
    assert _to_binance_interval(Timeframe.H4) == "4h"
    assert _to_binance_interval(Timeframe.MO1) == "1M"


def test_parse_klines_returns_standard_ohlcv_schema():
    payload = [
        [
            1704067200000,
            "42000.0",
            "43000.0",
            "41000.0",
            "42500.0",
            "123.45",
            1704153599999,
        ]
    ]

    df = _parse_klines(payload, "BTCUSDT")

    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume", "symbol"]
    assert df.loc[0, "symbol"] == "BTCUSDT"
    assert df.loc[0, "close"] == 42500.0
    assert df.loc[0, "volume"] == 123.45


def test_binance_capabilities_are_crypto_only_public_market_data():
    caps = BinanceProvider().capabilities()

    assert caps.name == "binance"
    assert caps.supported_markets == [Market.CRYPTO]
    assert caps.supports_intraday is True
    assert caps.supports_live is False

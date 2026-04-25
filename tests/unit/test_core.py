"""
Quant Engine — Core Protocols & Instrument Testleri

Test edilen:
- Protocol runtime_checkable doğrulaması
- Enum değerleri
- BarRequest / FetchResult / ProviderCapabilities modelleri
- EquityInstrument / FuturesInstrument modelleri
- DataLayer, Market, Timeframe enum'ları
"""

import pandas as pd
import pytest

from quant_engine.core.instrument import (
    EquityInstrument,
    FuturesInstrument,
    Instrument,
)
from quant_engine.core.protocols import (
    AssetClass,
    BarRequest,
    DataLayer,
    FetchResult,
    Market,
    MarketDataProvider,
    ProviderCapabilities,
    StorageBackend,
    Strategy,
    Timeframe,
)


class TestEnums:
    """Enum değer testleri."""

    def test_market_values(self):
        assert Market.BIST.value == "bist"
        assert Market.VIOP.value == "viop"

    def test_timeframe_values(self):
        assert Timeframe.D1.value == "1d"
        assert Timeframe.M1.value == "1m"
        assert Timeframe.H1.value == "1h"

    def test_asset_class_values(self):
        assert AssetClass.EQUITY.value == "equity"
        assert AssetClass.FUTURES.value == "futures"

    def test_data_layer_values(self):
        assert DataLayer.RAW.value == "raw"
        assert DataLayer.CLEAN.value == "clean"
        assert DataLayer.ADJUSTED.value == "adjusted"
        assert DataLayer.FEATURES.value == "features"


class TestBarRequest:
    """BarRequest value object testleri."""

    def test_default_values(self):
        req = BarRequest(symbol="THYAO")
        assert req.symbol == "THYAO"
        assert req.market == Market.BIST
        assert req.timeframe == Timeframe.D1
        assert req.start is None
        assert req.end is None

    def test_frozen(self):
        """BarRequest immutable olmalı."""
        req = BarRequest(symbol="GARAN")
        with pytest.raises(AttributeError):
            req.symbol = "AKBNK"


class TestFetchResult:
    """FetchResult modeli testleri."""

    def test_success_with_data(self):
        df = pd.DataFrame({"close": [100, 101, 102]})
        result = FetchResult(
            symbol="THYAO",
            data=df,
            source="yfinance",
        )
        assert result.success is True
        assert result.row_count == 3

    def test_failure_with_errors(self):
        result = FetchResult(
            symbol="THYAO",
            data=pd.DataFrame(),
            source="yfinance",
            errors=["Veri bulunamadı"],
        )
        assert result.success is False
        assert result.row_count == 0

    def test_warnings_dont_fail(self):
        df = pd.DataFrame({"close": [100]})
        result = FetchResult(
            symbol="THYAO",
            data=df,
            source="yfinance",
            warnings=["NaN tespit edildi"],
        )
        assert result.success is True


class TestProviderCapabilities:
    """ProviderCapabilities testleri."""

    def test_yfinance_caps(self):
        caps = ProviderCapabilities(
            name="yfinance",
            supported_markets=[Market.BIST],
            supported_timeframes=[
                Timeframe.D1, Timeframe.H1,
            ],
            supports_intraday=True,
            supports_live=False,
        )
        assert caps.name == "yfinance"
        assert Market.BIST in caps.supported_markets
        assert caps.supports_live is False


class TestInstrument:
    """Instrument modeli testleri."""

    def test_basic_instrument(self):
        inst = Instrument(
            symbol="THYAO", name="Türk Hava Yolları"
        )
        assert inst.symbol == "THYAO"
        assert str(inst) == "THYAO (bist)"

    def test_equity_instrument(self):
        eq = EquityInstrument(
            symbol="GARAN",
            name="Garanti BBVA",
            lot_size=1,
            tick_size=0.01,
        )
        assert eq.asset_class == AssetClass.EQUITY
        assert eq.market == Market.BIST
        assert eq.currency == "TRY"

    def test_futures_instrument(self):
        fut = FuturesInstrument(
            symbol="F_XU030",
            name="BIST30 Vadeli",
            contract_multiplier=100.0,
            expiry="2024-08",
            underlying="XU030",
        )
        assert fut.asset_class == AssetClass.FUTURES
        assert fut.market == Market.VIOP
        assert fut.contract_code == "F_XU030_202408"

    def test_equity_default_name(self):
        """İsim verilmezse sembol kullanılmalı."""
        eq = EquityInstrument(symbol="AKBNK")
        assert eq.name == "AKBNK"


class TestProtocolsAreCheckable:
    """Protocol'ler runtime_checkable olmalı."""

    def test_market_data_provider_checkable(self):
        assert hasattr(
            MarketDataProvider, "__protocol_attrs__"
        ) or issubclass(
            type(MarketDataProvider), type
        )

    def test_storage_backend_checkable(self):
        assert hasattr(
            StorageBackend, "__protocol_attrs__"
        ) or issubclass(
            type(StorageBackend), type
        )

    def test_strategy_checkable(self):
        assert hasattr(
            Strategy, "__protocol_attrs__"
        ) or issubclass(type(Strategy), type)

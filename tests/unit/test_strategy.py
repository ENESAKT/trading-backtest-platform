"""
Quant Engine — Strategy Framework Unit Testleri

Test edilen:
- İndikatörler (SMA, EMA, RSI, Bollinger, ATR, MACD)
- BaseStrategy arayüzü
- Strateji parametreleri
- Registry (kayıt, oluşturma, listeleme)
- SMA Crossover stratejisi
- RSI Reversion stratejisi
- Bollinger Reversion stratejisi
- Buy & Hold baseline
- Engine entegrasyonu (strategy.as_signal_func → engine.run)
"""

import numpy as np
import pandas as pd
import pytest

from quant_engine.backtest.domain import Portfolio
from quant_engine.backtest.engine import BacktestConfig, BacktestEngine
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    rsi,
    sma,
)
from quant_engine.strategy.registry import StrategyRegistry

# ---------------------------------------------------------------------------
# Test Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def price_series():
    """50 barlık yapay fiyat serisi."""
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(50) * 2)
    return pd.Series(prices, name="close")


@pytest.fixture
def ohlcv_data():
    """50 barlık yapay OHLCV verisi."""
    np.random.seed(42)
    n = 50
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    open_ = close + np.random.randn(n) * 0.5
    high = np.maximum(open_, close) + np.abs(np.random.randn(n))
    low = np.minimum(open_, close) - np.abs(np.random.randn(n))

    return pd.DataFrame({
        "date": pd.date_range("2024-01-02", periods=n, freq="B"),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(100_000, 5_000_000, n),
        "symbol": ["TEST"] * n,
    })


@pytest.fixture
def engine_config():
    """Test için backtest config."""
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,
        slippage_bps=0,
        max_position_pct=1.0,
        warm_up_bars=0,
    )


# ---------------------------------------------------------------------------
# İndikatör Testleri
# ---------------------------------------------------------------------------

class TestSMA:
    """Simple Moving Average testleri."""

    def test_sma_length(self, price_series):
        result = sma(price_series, 10)
        assert len(result) == len(price_series)

    def test_sma_first_values_nan(self, price_series):
        result = sma(price_series, 10)
        assert result.iloc[:9].isna().all()
        assert not pd.isna(result.iloc[9])

    def test_sma_manual_check(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(s, 3)
        assert result.iloc[2] == pytest.approx(2.0)  # (1+2+3)/3
        assert result.iloc[4] == pytest.approx(4.0)  # (3+4+5)/3

    def test_sma_invalid_period(self):
        with pytest.raises(ValueError):
            sma(pd.Series([1, 2, 3]), 0)


class TestEMA:
    """Exponential Moving Average testleri."""

    def test_ema_length(self, price_series):
        result = ema(price_series, 10)
        assert len(result) == len(price_series)

    def test_ema_no_nan(self, price_series):
        """EMA ilk değerden itibaren hesaplanır (adjust=False)."""
        result = ema(price_series, 10)
        assert not result.isna().any()

    def test_ema_responds_faster_than_sma(self, price_series):
        """EMA fiyat değişimlerine SMA'dan hızlı tepki verir."""
        ema_vals = ema(price_series, 10)
        sma_vals = sma(price_series, 10)
        # Son 10 barda fark olmalı
        diff = (ema_vals - sma_vals).dropna().abs()
        assert diff.sum() > 0


class TestRSI:
    """Relative Strength Index testleri."""

    def test_rsi_range(self, price_series):
        result = rsi(price_series, 14)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_rsi_period_nan(self, price_series):
        result = rsi(price_series, 14)
        assert result.iloc[:14].isna().all()

    def test_rsi_uptrend_high(self):
        """Sürekli yükselen seri → RSI yüksek olmalı."""
        s = pd.Series(range(1, 31), dtype=float)
        result = rsi(s, 14)
        assert result.iloc[-1] > 80

    def test_rsi_downtrend_low(self):
        """Sürekli düşen seri → RSI düşük olmalı."""
        s = pd.Series(range(30, 0, -1), dtype=float)
        result = rsi(s, 14)
        assert result.iloc[-1] < 20


class TestBollingerBands:
    """Bollinger Bands testleri."""

    def test_bands_structure(self, price_series):
        upper, middle, lower = bollinger_bands(price_series, 20)
        valid_idx = middle.dropna().index
        # Upper > Middle > Lower
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_middle_equals_sma(self, price_series):
        _, middle, _ = bollinger_bands(price_series, 20)
        sma_20 = sma(price_series, 20)
        pd.testing.assert_series_equal(middle, sma_20)


class TestATR:
    """Average True Range testleri."""

    def test_atr_positive(self, ohlcv_data):
        result = atr(
            ohlcv_data["high"],
            ohlcv_data["low"],
            ohlcv_data["close"],
            14,
        )
        valid = result.dropna()
        assert (valid > 0).all()


class TestMACD:
    """MACD testleri."""

    def test_macd_structure(self, price_series):
        macd_line, signal_line, histogram = macd(price_series)
        assert len(macd_line) == len(price_series)
        assert len(signal_line) == len(price_series)
        assert len(histogram) == len(price_series)

    def test_histogram_is_difference(self, price_series):
        macd_line, signal_line, histogram = macd(price_series)
        diff = macd_line - signal_line
        pd.testing.assert_series_equal(
            histogram, diff, check_names=False
        )


# ---------------------------------------------------------------------------
# BaseStrategy Testleri
# ---------------------------------------------------------------------------

class TestBaseStrategy:
    """BaseStrategy arayüz testleri."""

    def test_cannot_instantiate_abstract(self):
        """Soyut sınıf doğrudan oluşturulamaz."""
        with pytest.raises(TypeError):
            BaseStrategy()

    def test_custom_strategy(self, ohlcv_data):
        """Özel strateji oluşturulabilir."""

        class AlwaysBuy(BaseStrategy):
            name = "always_buy"

            @property
            def default_params(self):
                return {"threshold": 50}

            @property
            def warm_up_bars(self):
                return 0

            def generate_signals(self, data, bar_index, portfolio):
                pos = portfolio.get_or_create_position("TEST")
                if not pos.is_open:
                    return 1
                return 0

        strategy = AlwaysBuy()
        assert strategy.name == "always_buy"
        assert strategy.get_param("threshold") == 50

    def test_unknown_param_rejected(self):
        """Bilinmeyen parametre → ValueError."""

        class Simple(BaseStrategy):
            name = "simple"

            @property
            def default_params(self):
                return {"period": 10}

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        with pytest.raises(ValueError, match="Bilinmeyen"):
            Simple(params={"period": 20, "nonexistent": 5})

    def test_params_override(self):
        """Parametreler override edilebilir."""

        class Simple(BaseStrategy):
            name = "simple"

            @property
            def default_params(self):
                return {"period": 10, "threshold": 50}

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        s = Simple(params={"period": 20})
        assert s.get_param("period") == 20
        assert s.get_param("threshold") == 50  # default

    def test_as_signal_func(self, ohlcv_data):
        """as_signal_func() engine uyumlu fonksiyon döndürür."""

        class AlwaysZero(BaseStrategy):
            name = "zero"

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        strategy = AlwaysZero()
        signal_func = strategy.as_signal_func()
        portfolio = Portfolio(initial_capital=100_000)
        result = signal_func(ohlcv_data, 5, portfolio)
        assert result == 0


# ---------------------------------------------------------------------------
# Registry Testleri
# ---------------------------------------------------------------------------

class TestStrategyRegistry:
    """StrategyRegistry testleri."""

    def test_register_and_create(self):
        registry = StrategyRegistry()

        class TestStrat(BaseStrategy):
            name = "test_strat"

            @property
            def default_params(self):
                return {"period": 10}

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        registry.register(TestStrat)
        assert "test_strat" in registry

        instance = registry.create("test_strat", {"period": 20})
        assert instance.get_param("period") == 20

    def test_duplicate_registration_fails(self):
        registry = StrategyRegistry()

        class TestStrat(BaseStrategy):
            name = "dup_test"

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        registry.register(TestStrat)
        with pytest.raises(ValueError, match="zaten kayıtlı"):
            registry.register(TestStrat)

    def test_create_unknown_fails(self):
        registry = StrategyRegistry()
        with pytest.raises(KeyError, match="bulunamadı"):
            registry.create("nonexistent")

    def test_list_strategies(self):
        registry = StrategyRegistry()

        class TestStrat(BaseStrategy):
            name = "list_test"
            description = "Test stratejisi"

            @property
            def default_params(self):
                return {"x": 1}

            def generate_signals(self, data, bar_index, portfolio):
                return 0

        registry.register(TestStrat)
        strategies = registry.list_strategies()
        assert len(strategies) == 1
        assert strategies[0]["name"] == "list_test"
        assert strategies[0]["description"] == "Test stratejisi"

    def test_register_non_strategy_fails(self):
        registry = StrategyRegistry()
        with pytest.raises(TypeError):
            registry.register(int)


# ---------------------------------------------------------------------------
# Örnek Strateji Testleri
# ---------------------------------------------------------------------------

class TestBuyAndHold:
    """Buy & Hold stratejisi testleri."""

    def test_import_and_registry(self):
        from quant_engine.strategy.examples.buy_and_hold import BuyAndHold

        assert BuyAndHold.name == "buy_and_hold"
        assert BuyAndHold().warm_up_bars == 0

    def test_engine_integration(self, ohlcv_data, engine_config):
        from quant_engine.strategy.examples.buy_and_hold import BuyAndHold

        strategy = BuyAndHold()
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )
        assert len(result.fills) >= 1
        assert result.final_equity > 0
        assert len(result.equity_curve) == len(ohlcv_data)


class TestSmaCrossover:
    """SMA Crossover stratejisi testleri."""

    def test_import_and_defaults(self):
        from quant_engine.strategy.examples.sma_crossover import SmaCrossover

        s = SmaCrossover()
        assert s.name == "sma_crossover"
        assert s.get_param("fast_period") == 10
        assert s.get_param("slow_period") == 30
        assert s.warm_up_bars == 30

    def test_custom_params(self):
        from quant_engine.strategy.examples.sma_crossover import SmaCrossover

        s = SmaCrossover(params={"fast_period": 5, "slow_period": 20})
        assert s.get_param("fast_period") == 5
        assert s.warm_up_bars == 20

    def test_engine_integration(self, ohlcv_data, engine_config):
        from quant_engine.strategy.examples.sma_crossover import SmaCrossover

        strategy = SmaCrossover(params={"fast_period": 5, "slow_period": 15})
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )
        assert result.final_equity > 0
        # Equity curve verisi kadar olmalı
        assert len(result.equity_curve) == len(ohlcv_data)


class TestRsiReversion:
    """RSI Reversion stratejisi testleri."""

    def test_import_and_defaults(self):
        from quant_engine.strategy.examples.rsi_reversion import RsiReversion

        s = RsiReversion()
        assert s.name == "rsi_reversion"
        assert s.get_param("rsi_period") == 14
        assert s.get_param("oversold") == 30
        assert s.get_param("overbought") == 70

    def test_custom_params(self):
        from quant_engine.strategy.examples.rsi_reversion import RsiReversion

        s = RsiReversion(params={"oversold": 25, "overbought": 75})
        assert s.get_param("oversold") == 25
        assert s.get_param("overbought") == 75

    def test_engine_integration(self, ohlcv_data, engine_config):
        from quant_engine.strategy.examples.rsi_reversion import RsiReversion

        strategy = RsiReversion(
            params={"rsi_period": 5, "oversold": 35, "overbought": 65}
        )
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )
        assert result.final_equity > 0
        assert len(result.equity_curve) == len(ohlcv_data)


class TestBollingerReversion:
    """Bollinger Reversion stratejisi testleri."""

    def test_import_and_defaults(self):
        from quant_engine.strategy.examples.bollinger_reversion import (
            BollingerReversion,
        )

        s = BollingerReversion()
        assert s.name == "bollinger_reversion"
        assert s.get_param("period") == 20
        assert s.get_param("num_std") == 2.0
        assert s.get_param("exit_band") == "middle"
        assert s.warm_up_bars == 20

    def test_custom_params(self):
        from quant_engine.strategy.examples.bollinger_reversion import (
            BollingerReversion,
        )

        s = BollingerReversion(
            params={"period": 10, "num_std": 1.8, "exit_band": "upper"}
        )
        assert s.get_param("period") == 10
        assert s.get_param("num_std") == 1.8
        assert s.get_param("exit_band") == "upper"

    def test_invalid_exit_band(self):
        from quant_engine.strategy.examples.bollinger_reversion import (
            BollingerReversion,
        )

        s = BollingerReversion(params={"exit_band": "bad"})
        assert s.validate_params()

    def test_signal_rules(self):
        from quant_engine.strategy.examples.bollinger_reversion import (
            BollingerReversion,
        )

        data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-02", periods=8, freq="B"),
                "open": [100, 100, 100, 100, 100, 80, 90, 100],
                "high": [101, 101, 101, 101, 101, 82, 92, 102],
                "low": [99, 99, 99, 99, 99, 78, 88, 98],
                "close": [100, 100, 100, 100, 100, 80, 90, 100],
                "volume": [1_000_000] * 8,
                "symbol": ["TEST"] * 8,
            }
        )
        strategy = BollingerReversion(
            params={"period": 5, "num_std": 1.0, "exit_band": "middle"}
        )
        strategy.prepare(data)
        portfolio = Portfolio(initial_capital=100_000)

        assert strategy.generate_signals(data, 5, portfolio) == 1

        position = portfolio.get_or_create_position("TEST")
        position.quantity = 10
        position.avg_entry_price = 80.0
        position.total_cost_basis = 800.0
        assert strategy.generate_signals(data, 7, portfolio) == -1

    def test_engine_integration(self, ohlcv_data, engine_config):
        from quant_engine.strategy.examples.bollinger_reversion import (
            BollingerReversion,
        )

        strategy = BollingerReversion(
            params={"period": 10, "num_std": 1.5, "exit_band": "middle"}
        )
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )
        assert result.final_equity > 0
        assert len(result.equity_curve) == len(ohlcv_data)


# ---------------------------------------------------------------------------
# Metrics Testleri
# ---------------------------------------------------------------------------

class TestMetrics:
    """Performans metrikleri testleri."""

    def test_empty_equity_curve(self):
        from quant_engine.backtest.metrics import calculate_metrics

        metrics = calculate_metrics([], [], 100_000)
        assert metrics.total_return_pct == 0.0
        assert metrics.final_equity == 0.0

    def test_metrics_with_backtest(self, ohlcv_data, engine_config):
        from quant_engine.backtest.metrics import calculate_metrics
        from quant_engine.strategy.examples.buy_and_hold import BuyAndHold

        strategy = BuyAndHold()
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )

        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            engine_config.initial_capital,
        )

        # Temel kontroller
        assert metrics.initial_capital == engine_config.initial_capital
        assert metrics.final_equity > 0
        assert metrics.max_drawdown_pct >= 0
        # Exposure > 0 (Buy & Hold pozisyon açıyor)
        assert metrics.exposure_pct > 0

    def test_metrics_summary_string(self, ohlcv_data, engine_config):
        from quant_engine.backtest.metrics import calculate_metrics
        from quant_engine.strategy.examples.buy_and_hold import BuyAndHold

        strategy = BuyAndHold()
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )

        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            engine_config.initial_capital,
        )

        summary = metrics.summary()
        assert "PERFORMANS METRİKLERİ" in summary
        assert "Sharpe" in summary

    def test_metrics_to_dict(self, ohlcv_data, engine_config):
        from quant_engine.backtest.metrics import calculate_metrics
        from quant_engine.strategy.examples.buy_and_hold import BuyAndHold

        strategy = BuyAndHold()
        engine = BacktestEngine(engine_config)
        result = engine.run(
            ohlcv_data,
            strategy.as_signal_func(),
            symbol="TEST",
        )

        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            engine_config.initial_capital,
        )

        d = metrics.to_dict()
        assert isinstance(d, dict)
        assert "sharpe_ratio" in d
        assert "total_return_pct" in d

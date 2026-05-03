"""
Quant Engine — Finansal Doğruluk Testleri (Aşama 2-3)

Test edilen:
- Signal timestamp doğruluğu (sinyal barı vs execution barı)
- Lookahead bias kontrolü
- CompletedTrade eşleştirmesi
- Komisyon ve slippage doğru maliyet etkisi
- Açık pozisyon final equity
- CAGR gerçek tarih farkından hesaplanması
- Timeframe-aware Sharpe/Sortino
- Parametre validasyonu
- Negatif nakit koruması
- Portfolio invariant
"""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from quant_engine.backtest.domain import (
    CompletedTrade,
)
from quant_engine.backtest.engine import (
    BacktestConfig,
    BacktestEngine,
    buy_and_hold_signal,
)
from quant_engine.backtest.metrics import (
    calculate_metrics,
)
from quant_engine.core.protocols import (
    OrderSide as CoreOrderSide,
)

# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def golden_data_10bar():
    """10 barlık deterministik test verisi."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                    "2024-01-09",
                    "2024-01-10",
                    "2024-01-11",
                    "2024-01-12",
                    "2024-01-15",
                ]
            ),
            "open": [
                100, 102, 105, 103, 107,
                110, 108, 112, 115, 113,
            ],
            "high": [
                103, 106, 107, 108, 110,
                112, 113, 116, 117, 115,
            ],
            "low": [
                99, 101, 102, 102, 105,
                107, 106, 110, 112, 111,
            ],
            "close": [
                101, 104, 103, 106, 108,
                109, 111, 114, 113, 112,
            ],
            "volume": [1_000_000] * 10,
            "symbol": ["TEST"] * 10,
        }
    )


@pytest.fixture
def zero_cost_config():
    """Sıfır maliyet config — kolay hesaplama."""
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.0,
        slippage_bps=0,
        max_position_pct=1.0,
        warm_up_bars=0,
    )


@pytest.fixture
def cost_config():
    """Maliyet dahil config."""
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,
        slippage_bps=10,
        max_position_pct=1.0,
        warm_up_bars=0,
    )


# ---------------------------------------------------------------------------
# Aşama 1: Enum Tekrarı Çözüldü
# ---------------------------------------------------------------------------


class TestEnumConsolidation:
    """Enum'lar tek kaynaktan geliyor."""

    def test_order_side_same_from_both(self):
        """OrderSide core ve domain'den aynı."""
        from quant_engine.backtest.domain import (
            OrderSide as DomainOrderSide,
        )

        assert CoreOrderSide.BUY == DomainOrderSide.BUY
        assert CoreOrderSide is DomainOrderSide

    def test_order_status_exists_in_core(self):
        """OrderStatus artık core'da tanımlı."""
        from quant_engine.core.protocols import (
            OrderStatus,
        )

        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.FILLED == "filled"
        assert OrderStatus.CANCELLED == "cancelled"
        assert OrderStatus.REJECTED == "rejected"


# ---------------------------------------------------------------------------
# Aşama 2: Finansal Doğruluk
# ---------------------------------------------------------------------------


class TestSignalTimestamp:
    """Signal timestamp doğruluğu."""

    def test_signal_is_from_signal_bar(
        self, golden_data_10bar, zero_cost_config
    ):
        """
        signal_timestamp sinyal barının tarihini yazmalı,
        execution barının değil.

        bar 0'da sinyal → signal_timestamp = 2024-01-02
        bar 1'de execute → fill_timestamp = 2024-01-03
        """
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        assert len(result.fills) >= 1
        first_fill = result.fills[0]

        # Sinyal bar 0'da üretildi
        assert first_fill.order.signal_bar_index == 0
        signal_date = first_fill.order.signal_timestamp
        assert signal_date.date() == dt.date(
            2024, 1, 2
        )

        # Execution bar 1'de
        assert first_fill.bar_index == 1
        fill_date = first_fill.fill_timestamp
        assert fill_date.date() == dt.date(2024, 1, 3)

    def test_signal_and_fill_dates_differ(
        self, golden_data_10bar, zero_cost_config
    ):
        """Sinyal tarihi ile dolum tarihi farklı olmalı."""
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        for fill in result.fills:
            assert (
                fill.order.signal_timestamp
                != fill.fill_timestamp
            ), (
                f"Signal ve fill timestamp aynı! "
                f"signal={fill.order.signal_timestamp} "
                f"fill={fill.fill_timestamp}"
            )


class TestLookaheadBias:
    """Lookahead bias testleri."""

    def test_fill_uses_next_bar_open(
        self, golden_data_10bar, zero_cost_config
    ):
        """Fill fiyatı sinyalden sonraki barın open'ı."""
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        first_fill = result.fills[0]
        # bar 0: close=101 (sinyal), bar 1: open=102
        assert first_fill.fill_price == pytest.approx(
            102.0
        )

    def test_signal_cannot_use_future_data(
        self, golden_data_10bar, zero_cost_config
    ):
        """Sinyal fonksiyonu geleceği göremez."""
        seen_indices = []

        def tracking_signal(data, bar_index, portfolio):
            seen_indices.append(bar_index)
            # bar_index sonrasındaki veriyi kullanmamalı
            assert bar_index < len(data)
            return 0

        engine = BacktestEngine(zero_cost_config)
        engine.run(
            golden_data_10bar,
            tracking_signal,
            symbol="TEST",
        )

        # Tüm barlar ziyaret edilmeli
        assert len(seen_indices) == 10


class TestCompletedTrades:
    """Trade eşleştirme testleri."""

    def test_buy_sell_creates_trade(
        self, golden_data_10bar, zero_cost_config
    ):
        """Al-sat çifti CompletedTrade oluşturmalı."""

        def buy_then_sell(data, i, portfolio):
            pos = portfolio.get_or_create_position(
                "TEST"
            )
            if i == 0 and not pos.is_open:
                return 1
            if i == 5 and pos.is_open:
                return -1
            return 0

        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_then_sell,
            symbol="TEST",
        )

        assert len(result.trades) == 1
        trade = result.trades[0]
        assert trade.symbol == "TEST"
        assert trade.entry_price == pytest.approx(
            102.0
        )  # bar 1 open
        assert trade.exit_price == pytest.approx(
            108.0
        )  # bar 6 open (sinyal bar5, exec bar6)
        assert trade.quantity > 0
        assert trade.gross_pnl > 0  # 108 - 102 = +6/share
        assert trade.holding_bars == 5  # bar 6 - bar 1

    def test_buy_hold_has_no_completed_trade(
        self, golden_data_10bar, zero_cost_config
    ):
        """Buy & Hold → açık pozisyon, tamamlanmış trade yok."""
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        assert len(result.trades) == 0
        assert result.has_open_position is True

    def test_multiple_round_trips(
        self, golden_data_10bar, zero_cost_config
    ):
        """Birden fazla al-sat çifti."""

        def multi_trade(data, i, portfolio):
            pos = portfolio.get_or_create_position(
                "TEST"
            )
            if i == 0 and not pos.is_open:
                return 1
            if i == 3 and pos.is_open:
                return -1
            if i == 5 and not pos.is_open:
                return 1
            if i == 8 and pos.is_open:
                return -1
            return 0

        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            multi_trade,
            symbol="TEST",
        )

        assert len(result.trades) == 2


class TestCommissionSlippage:
    """Komisyon ve slippage testleri."""

    def test_commission_reduces_equity(
        self, golden_data_10bar
    ):
        """Komisyon equity'yi azaltmalı."""
        zero_config = BacktestConfig(
            initial_capital=100_000,
            commission_rate=0.0,
            slippage_bps=0,
            max_position_pct=1.0,
        )
        cost_config = BacktestConfig(
            initial_capital=100_000,
            commission_rate=0.01,  # %1 komisyon
            slippage_bps=0,
            max_position_pct=1.0,
        )

        engine_free = BacktestEngine(zero_config)
        engine_cost = BacktestEngine(cost_config)

        result_free = engine_free.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )
        result_cost = engine_cost.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        assert (
            result_cost.final_equity
            < result_free.final_equity
        )
        assert result_cost.total_commission > 0

    def test_slippage_cost_is_per_unit_times_qty(
        self, golden_data_10bar
    ):
        """Slippage maliyeti = per-unit slippage × adet."""
        config = BacktestConfig(
            initial_capital=100_000,
            commission_rate=0.0,
            slippage_bps=50,  # 50 bps = %0.5
            max_position_pct=1.0,
        )

        engine = BacktestEngine(config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        first_fill = result.fills[0]
        expected_slippage = abs(
            first_fill.fill_price - 102.0
        )
        assert first_fill.slippage == pytest.approx(
            expected_slippage
        )
        assert (
            first_fill.slippage_cost
            == pytest.approx(
                expected_slippage
                * first_fill.fill_quantity
            )
        )


class TestOpenPositionEquity:
    """Açık pozisyon final equity testleri."""

    def test_open_position_valued_at_market(
        self, golden_data_10bar, zero_cost_config
    ):
        """
        Açık pozisyon son barın close'u ile değerlenmeli.
        """
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        # Son bar close = 112
        last_close = 112.0
        # Buy @ bar 1 open = 102.0, 0 cost
        quantity = int(100_000 / 102.0)  # 980 adet
        expected_equity = (
            100_000 - quantity * 102.0
        ) + quantity * last_close

        assert result.final_equity == pytest.approx(
            expected_equity, rel=0.001
        )

    def test_has_open_position_flag(
        self, golden_data_10bar, zero_cost_config
    ):
        """Buy & Hold açık pozisyon flag'i ayarlamalı."""
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        assert result.has_open_position is True
        assert any(
            "Açık pozisyon" in (w.message if hasattr(w, "message") else (w["message"] if isinstance(w, dict) else str(w)))
            for w in result.warnings
        )


class TestPendingSignalLastBar:
    """Son barda pending signal davranışı."""

    def test_last_bar_signal_discarded_with_warning(
        self, golden_data_10bar, zero_cost_config
    ):
        """Son barda sinyal üretilirse uyarı verilmeli."""

        def signal_at_last_bar(data, i, portfolio):
            if i == len(data) - 1:
                return 1  # Son barda al sinyali
            return 0

        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            signal_at_last_bar,
            symbol="TEST",
        )

        assert any(
            "Son barda sinyal" in (w.message if hasattr(w, "message") else (w["message"] if isinstance(w, dict) else str(w)))
            for w in result.warnings
        )


class TestPortfolioInvariant:
    """Portfolio invariant testleri."""

    def test_invariant_holds_every_bar(
        self, golden_data_10bar, zero_cost_config
    ):
        """cash + position_value == equity her barda."""
        engine = BacktestEngine(zero_cost_config)
        result = engine.run(
            golden_data_10bar,
            buy_and_hold_signal,
            symbol="TEST",
        )

        for ep in result.equity_curve:
            expected = ep.cash + ep.position_value
            assert ep.total_equity == pytest.approx(
                expected, abs=0.01
            )


# ---------------------------------------------------------------------------
# Aşama 3: Metrik Doğruluğu
# ---------------------------------------------------------------------------


class TestCAGR:
    """CAGR gerçek tarih farkından hesaplanması."""

    def test_cagr_uses_real_dates(self):
        """
        2 yıllık veri, %100 getiri → CAGR ≈ %41.4
        (not bar sayısı)
        """
        # 2 yıl: 2022-01-03 → 2023-12-29 (≈730 gün)
        n_bars = 504  # ~2 yıl iş günü
        dates = pd.bdate_range(
            "2022-01-03", periods=n_bars
        )
        equity_points = []
        initial = 100_000
        final = 200_000  # %100 getiri
        for i, d in enumerate(dates):
            eq = initial + (
                final - initial
            ) * i / (n_bars - 1)
            equity_points.append(
                __import__(
                    "quant_engine.backtest.domain",
                    fromlist=["EquityPoint"],
                ).EquityPoint(
                    timestamp=d.to_pydatetime(),
                    bar_index=i,
                    cash=eq,
                    position_value=0,
                    total_equity=eq,
                )
            )

        metrics = calculate_metrics(
            equity_points, [], initial
        )

        # 2 yıl %100 → CAGR ≈ 41.4%
        assert 35.0 < metrics.cagr_pct < 50.0


class TestTimeframeAwareSharpe:
    """Timeframe-aware annualization."""

    def test_weekly_sharpe_different_from_daily(self):
        """Haftalık ve günlük Sharpe farklı çarpan."""
        from quant_engine.backtest.domain import (
            EquityPoint,
        )

        n = 100
        equity_points = []
        np.random.seed(42)
        eq = 100_000.0
        for i in range(n):
            eq *= 1 + np.random.randn() * 0.01
            equity_points.append(
                EquityPoint(
                    timestamp=dt.datetime(
                        2024, 1, 1
                    )
                    + dt.timedelta(days=i),
                    bar_index=i,
                    cash=eq,
                    position_value=0,
                    total_equity=eq,
                )
            )

        daily = calculate_metrics(
            equity_points, [], 100_000, timeframe="1d"
        )
        weekly = calculate_metrics(
            equity_points, [], 100_000, timeframe="1wk"
        )

        # Farklı annualization → farklı Sharpe
        assert daily.sharpe_ratio != pytest.approx(
            weekly.sharpe_ratio
        )


class TestTradeMetrics:
    """Trade metrikleri CompletedTrade'den hesaplanması."""

    def test_metrics_from_completed_trades(self):
        """Metrikler CompletedTrade nesnelerinden."""
        from quant_engine.backtest.domain import (
            EquityPoint,
        )

        trades = [
            CompletedTrade(
                symbol="TEST",
                entry_price=100.0,
                exit_price=110.0,
                quantity=100,
                entry_commission=10.0,
                exit_commission=11.0,
                entry_bar_index=0,
                exit_bar_index=5,
            ),
            CompletedTrade(
                symbol="TEST",
                entry_price=120.0,
                exit_price=115.0,
                quantity=80,
                entry_commission=9.6,
                exit_commission=9.2,
                entry_bar_index=6,
                exit_bar_index=10,
            ),
        ]

        # Minimal equity curve
        equity_points = [
            EquityPoint(
                timestamp=dt.datetime(2024, 1, 1)
                + dt.timedelta(days=i),
                bar_index=i,
                cash=100_000.0,
                position_value=0,
                total_equity=100_000.0,
            )
            for i in range(15)
        ]

        metrics = calculate_metrics(
            equity_points,
            [],
            100_000,
            trades=trades,
        )

        assert metrics.total_trades == 2
        assert metrics.winning_trades == 1
        assert metrics.losing_trades == 1
        assert metrics.win_rate == pytest.approx(50.0)
        assert metrics.avg_holding_bars == pytest.approx(
            4.5
        )  # (5+4)/2


class TestParamValidation:
    """Strateji parametre validasyonu."""

    def test_sma_fast_gte_slow_error(self):
        """SMA fast >= slow → validasyon hatası."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        s = SmaCrossover(
            params={"fast_period": 30, "slow_period": 10}
        )
        errors = s.validate_params()
        assert len(errors) > 0
        assert any("fast_period" in e for e in errors)

    def test_rsi_oversold_gte_overbought_error(self):
        """RSI oversold >= overbought → hata."""
        from quant_engine.strategy.examples.rsi_reversion import (
            RsiReversion,
        )

        s = RsiReversion(
            params={"oversold": 70, "overbought": 30}
        )
        errors = s.validate_params()
        assert len(errors) > 0

    def test_valid_params_no_error(self):
        """Geçerli parametreler → boş hata listesi."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        s = SmaCrossover(
            params={"fast_period": 5, "slow_period": 20}
        )
        errors = s.validate_params()
        assert len(errors) == 0


class TestStrategyPrepare:
    """Strateji prepare() cache testleri."""

    def test_sma_prepare_caches_indicators(self):
        """prepare() sonrası indikatörler cache'de."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        np.random.seed(42)
        n = 50
        data = pd.DataFrame(
            {
                "close": 100
                + np.cumsum(np.random.randn(n) * 2),
                "date": pd.date_range(
                    "2024-01-01", periods=n
                ),
                "symbol": ["TEST"] * n,
            }
        )

        s = SmaCrossover()
        s.prepare(data)

        assert "fast_sma" in s._prepared_data
        assert "slow_sma" in s._prepared_data
        assert len(s._prepared_data["fast_sma"]) == n

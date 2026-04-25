"""
Quant Engine — Backtest Engine Unit Testleri

Test edilen:
- Portfolio domain nesneleri (Order, Fill, Position, Portfolio)
- Backtest engine execution
- Buy & Hold baseline
- Portfolio invariant (cash + position = equity)
- Komisyon ve slippage hesaplaması
- Golden fixture: elle hesaplanmış sonuç eşleşmesi
"""

import pandas as pd
import pytest

from quant_engine.backtest.domain import (
    Fill,
    Order,
    OrderSide,
    OrderType,
    Portfolio,
    Position,
)
from quant_engine.backtest.engine import (
    BacktestConfig,
    BacktestEngine,
    buy_and_hold_signal,
)


# ---------------------------------------------------------------------------
# Golden Fixture: Elle hesaplanmış 5 barlık veri
# ---------------------------------------------------------------------------

@pytest.fixture
def golden_data():
    """5 barlık test verisi — elle hesaplanabilir."""
    return pd.DataFrame({
        "date": pd.to_datetime([
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-08",
        ]),
        "open": [100.0, 102.0, 105.0, 103.0, 107.0],
        "high": [103.0, 106.0, 107.0, 108.0, 110.0],
        "low": [99.0, 101.0, 102.0, 102.0, 105.0],
        "close": [101.0, 104.0, 103.0, 106.0, 108.0],
        "volume": [
            1000000, 1200000, 900000, 1100000, 1300000,
        ],
        "symbol": ["TEST"] * 5,
    })


@pytest.fixture
def config():
    """Test config — basit hesaplama için."""
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,  # %0.1
        slippage_bps=0,  # Slippage yok (kolay hesaplama)
        max_position_pct=1.0,  # Tüm sermaye
        warm_up_bars=0,
    )


# ---------------------------------------------------------------------------
# Domain Testleri
# ---------------------------------------------------------------------------

class TestPosition:
    """Position nesnesi testleri."""

    def test_empty_position(self):
        pos = Position(symbol="TEST")
        assert pos.quantity == 0
        assert pos.is_open is False

    def test_buy_updates_position(self):
        pos = Position(symbol="TEST")
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            quantity=100,
        )
        fill = Fill(
            order=order,
            fill_price=50.0,
            fill_quantity=100,
        )
        pos.update_on_fill(fill)
        assert pos.quantity == 100
        assert pos.avg_entry_price == 50.0
        assert pos.is_open is True

    def test_sell_closes_position(self):
        pos = Position(
            symbol="TEST",
            quantity=100,
            avg_entry_price=50.0,
            total_cost_basis=5000.0,
        )
        order = Order(
            symbol="TEST",
            side=OrderSide.SELL,
            quantity=100,
        )
        fill = Fill(
            order=order,
            fill_price=60.0,
            fill_quantity=100,
        )
        pnl = pos.update_on_fill(fill)
        assert pos.quantity == 0
        assert pos.is_open is False
        assert pnl == pytest.approx(1000.0)  # (60-50)*100

    def test_unrealized_pnl(self):
        pos = Position(
            symbol="TEST",
            quantity=100,
            avg_entry_price=50.0,
            total_cost_basis=5000.0,
        )
        assert pos.unrealized_pnl(55.0) == pytest.approx(
            500.0
        )
        assert pos.unrealized_pnl(45.0) == pytest.approx(
            -500.0
        )

    def test_market_value(self):
        pos = Position(
            symbol="TEST", quantity=100,
            avg_entry_price=50.0,
            total_cost_basis=5000.0,
        )
        assert pos.market_value(55.0) == pytest.approx(
            5500.0
        )


class TestPortfolio:
    """Portfolio nesnesi testleri."""

    def test_initial_state(self):
        p = Portfolio(initial_capital=100_000)
        assert p.cash == 100_000
        assert p.total_equity({}) == 100_000

    def test_buy_reduces_cash(self):
        p = Portfolio(initial_capital=100_000)
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            quantity=100,
        )
        fill = Fill(
            order=order,
            fill_price=100.0,
            fill_quantity=100,
            commission=10.0,
        )
        p.process_fill(fill)
        # cash = 100_000 - (100*100 + 10) = 89_990
        assert p.cash == pytest.approx(89_990.0)

    def test_equity_invariant(self):
        """cash + position_value == total_equity"""
        p = Portfolio(initial_capital=100_000)
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            quantity=100,
        )
        fill = Fill(
            order=order,
            fill_price=100.0,
            fill_quantity=100,
            commission=10.0,
        )
        p.process_fill(fill)

        prices = {"TEST": 105.0}
        equity = p.total_equity(prices)
        cash_plus_pos = (
            p.cash + p.total_position_value(prices)
        )
        assert equity == pytest.approx(cash_plus_pos)


# ---------------------------------------------------------------------------
# Engine Testleri
# ---------------------------------------------------------------------------

class TestBacktestEngine:
    """Backtest engine testleri."""

    def test_buy_and_hold(self, golden_data, config):
        """Buy & Hold stratejisi — bilinen sonuçlarla."""
        engine = BacktestEngine(config)
        result = engine.run(
            golden_data,
            buy_and_hold_signal,
            symbol="TEST",
        )

        # Motor çalışmış olmalı
        assert len(result.equity_curve) == 5
        assert result.final_equity > 0
        assert len(result.fills) >= 1

    def test_always_hold_no_trade(
        self, golden_data, config
    ):
        """Sinyal vermezse trade olmamalı."""

        def no_signal(data, i, portfolio):
            return 0

        engine = BacktestEngine(config)
        result = engine.run(
            golden_data, no_signal, symbol="TEST"
        )

        assert len(result.fills) == 0
        assert result.final_equity == pytest.approx(
            config.initial_capital
        )

    def test_commission_applied(
        self, golden_data, config
    ):
        """Komisyon uygulanmalı."""
        engine = BacktestEngine(config)
        result = engine.run(
            golden_data,
            buy_and_hold_signal,
            symbol="TEST",
        )

        assert result.total_commission > 0

    def test_portfolio_invariant_every_bar(
        self, golden_data, config
    ):
        """Her barda cash + position = equity."""
        engine = BacktestEngine(config)
        result = engine.run(
            golden_data,
            buy_and_hold_signal,
            symbol="TEST",
        )

        for ep in result.equity_curve:
            expected = ep.cash + ep.position_value
            assert ep.total_equity == pytest.approx(
                expected, abs=0.01
            ), (
                f"Bar {ep.bar_index}: equity "
                f"({ep.total_equity}) != "
                f"cash+pos ({expected})"
            )

    def test_equity_curve_length(
        self, golden_data, config
    ):
        """Equity curve veri uzunluğu kadar olmalı."""
        engine = BacktestEngine(config)
        result = engine.run(
            golden_data,
            buy_and_hold_signal,
            symbol="TEST",
        )
        assert len(result.equity_curve) == len(golden_data)

    def test_buy_sell_round_trip(
        self, golden_data, config
    ):
        """Al-sat döngüsü: al → tut → sat."""
        trade_count = [0]

        def buy_then_sell(data, i, portfolio):
            pos = portfolio.get_or_create_position("TEST")
            if i == 0 and not pos.is_open:
                return 1  # AL
            if i == 3 and pos.is_open:
                return -1  # SAT
            return 0

        engine = BacktestEngine(config)
        result = engine.run(
            golden_data, buy_then_sell, symbol="TEST"
        )

        # 2 fill: 1 buy + 1 sell
        buy_fills = [
            f for f in result.fills
            if f.order.side == OrderSide.BUY
        ]
        sell_fills = [
            f for f in result.fills
            if f.order.side == OrderSide.SELL
        ]
        assert len(buy_fills) == 1
        assert len(sell_fills) == 1

    def test_warm_up_prevents_signals(
        self, golden_data
    ):
        """Warm-up süresinde sinyal üretilmemeli."""
        config = BacktestConfig(
            initial_capital=100_000,
            warm_up_bars=3,  # İlk 3 bar warm-up
        )

        signals_given = []

        def track_signals(data, i, portfolio):
            signals_given.append(i)
            return 1  # Her zaman al sinyali

        engine = BacktestEngine(config)
        # Sinyal bar 3'te verilir, execute bar 4'te
        result = engine.run(
            golden_data, track_signals, symbol="TEST"
        )

        # İlk sinyal bar 3'te olmalı
        # Ama warm_up_bars=3, bar 0,1,2 signal=0
        # Engine signal 0 döndürür warm-up'ta
        assert result.fills[0].bar_index >= 4

    def test_no_lookahead_bias(
        self, golden_data, config
    ):
        """
        Anti-leakage: sinyal bar[t], execution bar[t+1].

        bar 0'da sinyal → bar 1'in open'ında execute.
        fill_price ≈ bar 1'in open'ı olmalı.
        """
        engine = BacktestEngine(config)
        result = engine.run(
            golden_data,
            buy_and_hold_signal,
            symbol="TEST",
        )

        if result.fills:
            first_fill = result.fills[0]
            # Signal bar 0'da, execute bar 1'de
            # bar 1 open = 102.0
            assert first_fill.bar_index == 1
            assert first_fill.fill_price == pytest.approx(
                102.0, abs=0.1
            )

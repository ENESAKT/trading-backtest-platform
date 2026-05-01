import pandas as pd

from quant_engine.backtest.domain import (
    Fill,
    Order,
    OrderSide,
    Position,
)
from quant_engine.backtest.engine import BacktestConfig, BacktestEngine


def test_short_selling_position_math():
    pos = Position("TEST")

    # 1. Short Sell 100 shares @ 100.0
    sell_order = Order("TEST", OrderSide.SELL, 100)
    sell_fill = Fill(sell_order, 100.0, 100)

    realized = pos.update_on_fill(sell_fill)

    assert pos.quantity == -100
    assert pos.avg_entry_price == 100.0
    assert realized == 0.0

    # Market price goes to 90 (we are making money, +10 per share)
    assert pos.market_value(90.0) == -9000.0
    assert pos.unrealized_pnl(90.0) == 1000.0

    # 2. Buy back 100 shares @ 90.0 (Close Short)
    buy_order = Order("TEST", OrderSide.BUY, 100)
    buy_fill = Fill(buy_order, 90.0, 100)

    realized = pos.update_on_fill(buy_fill)

    assert pos.quantity == 0
    assert realized == 1000.0


def test_intent_engine_short_cover_pnl():
    data = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC"),
            "symbol": ["TEST"] * 5,
            "open": [100.0, 100.0, 95.0, 90.0, 88.0],
            "high": [101.0, 101.0, 96.0, 91.0, 89.0],
            "low": [99.0, 99.0, 94.0, 89.0, 87.0],
            "close": [100.0, 96.0, 92.0, 89.0, 88.0],
            "volume": [1000] * 5,
        }
    )

    def intent(_data, i, _portfolio):
        if i == 0:
            return "SHORT"
        if i == 2:
            return "COVER"
        return "HOLD"

    engine = BacktestEngine(
        BacktestConfig(
            initial_capital=10_000,
            commission_rate=0,
            slippage_bps=0,
            max_position_pct=1.0,
            allow_short=True,
        )
    )
    result = engine.run_intents(data, intent, symbol="TEST")

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.side == OrderSide.SELL
    assert trade.net_pnl > 0
    assert result.final_equity > 10_000

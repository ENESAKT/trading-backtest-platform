import datetime as dt
import pandas as pd
import pytest

from quant_engine.backtest.domain import (
    Fill, Order, OrderSide, Position
)

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


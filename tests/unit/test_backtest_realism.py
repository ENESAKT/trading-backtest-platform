import pytest
import json
from quant_engine.backtest.realism import (
    fixed_bps_slippage,
    fixed_tick_slippage,
    volume_capacity_warning,
    build_assumption_card
)

def test_fixed_bps_slippage():
    # 100 price, 50 bps = 0.5% = 0.5
    assert fixed_bps_slippage(100.0, "BUY", 50.0) == 100.5
    assert fixed_bps_slippage(100.0, "COVER", 50.0) == 100.5
    assert fixed_bps_slippage(100.0, "SELL", 50.0) == 99.5
    assert fixed_bps_slippage(100.0, "SHORT", 50.0) == 99.5
    
    # Negative price fallback
    assert fixed_bps_slippage(-10.0, "BUY", 50.0) == -10.0
    
    # Unknown side fallback
    assert fixed_bps_slippage(100.0, "UNKNOWN", 50.0) == 100.0

def test_fixed_tick_slippage():
    # 100 price, tick=0.01, ticks=2 => 0.02 slippage
    assert fixed_tick_slippage(100.0, "BUY", 0.01, 2) == 100.02
    assert fixed_tick_slippage(100.0, "SELL", 0.01, 2) == 99.98
    assert fixed_tick_slippage(100.0, "SHORT", 0.01, 2) == 99.98
    
    # Price cannot drop below 0
    assert fixed_tick_slippage(0.01, "SELL", 0.01, 2) == 0.0

def test_volume_capacity_warning():
    # order_value=1000, avg_vol=10000 (10%). limit is 5% -> Warning
    warn = volume_capacity_warning(1000.0, 10000.0, 5.0)
    assert warn is not None
    assert "exceeds max participation limit" in warn
    
    # order_value=1000, avg_vol=10000 (10%). limit is 15% -> None
    assert volume_capacity_warning(1000.0, 10000.0, 15.0) is None
    
    # zero vol
    assert volume_capacity_warning(1000.0, 0.0, 5.0) == "Market volume is zero or negative, illiquid symbol."

def test_build_assumption_card():
    card = build_assumption_card(
        slippage_bps=10.0,
        commission_rate=0.0004,
        is_short_bist=True
    )
    assert card["slippage_bps"] == 10.0
    assert card["commission_rate"] == 0.0004
    assert card["is_short_bist"] is True
    assert len(card["warnings"]) == 1
    assert "SHORT on BIST" in card["warnings"][0]

    # Should be json serializable
    dumped = json.dumps(card)
    assert "10.0" in dumped

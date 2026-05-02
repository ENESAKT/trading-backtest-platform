import numpy as np
import pandas as pd

from quant_engine.research.paper_ops import (
    generate_preflight_checklist,
    get_robot_summary,
    is_safe_to_trade_gap,
    kill_all_robots,
    kill_robot,
    process_signal_action,
    reduce_risk_limit,
)


def test_get_robot_summary():
    state = {
        "robot_id": "r1",
        "strategy_id": "s1",
        "pnl_pct": "2.5", # Should be cast to float
        "warnings": ["Low volume"]
    }
    res = get_robot_summary(state)
    assert res["robot_id"] == "r1"
    assert res["pnl_pct"] == 2.5
    assert len(res["warnings"]) == 1

def test_kill_switches():
    robots = [
        {"robot_id": "r1", "status": "active"},
        {"robot_id": "r2", "status": "stopped"},
        {"robot_id": "r3", "status": "active"}
    ]

    res_all = kill_all_robots(robots)
    assert res_all["affected_count"] == 2
    assert len(res_all["commands"]) == 2

    res_one = kill_robot("r1", robots)
    assert res_one["action"] == "stop"

    res_stopped = kill_robot("r2", robots)
    assert res_stopped["action"] == "none"

def test_reduce_risk_limit():
    state = {"robot_id": "r1", "daily_risk_limit": 50.0}

    res_ok = reduce_risk_limit(state, 30.0)
    assert res_ok["action"] == "update_limit"
    assert res_ok["new_limit"] == 30.0

    res_rej = reduce_risk_limit(state, 60.0)
    assert res_rej["action"] == "rejected"

def test_preflight_checklist():
    metrics = {
        "has_real_data": True,
        "bar_count": 500,
        "wfa_passed": True,
        "monte_carlo_passed": True,
        "has_slippage": True,
        "avg_volume": 50000, # Triggers liquidity warning
        "market": "BIST",
        "allows_short": True # Triggers short bist warning
    }
    res = generate_preflight_checklist(metrics)
    assert res["checklist"]["liquidity_warning"] is True
    assert res["checklist"]["short_bist_warning"] is True
    assert res["ready_to_start"] is False # Because of liquidity warning

def test_process_signal_action():
    sig_hist = {"type": "buy", "is_live_bar": False, "mode": "trade"}
    res_hist = process_signal_action(sig_hist)
    assert res_hist["action"] == "none"

    sig_alarm = {"type": "buy", "is_live_bar": True, "mode": "alarm_only"}
    res_alarm = process_signal_action(sig_alarm)
    assert res_alarm["action"] == "alarm"

    sig_trade = {"type": "sell", "is_live_bar": True, "mode": "trade"}
    res_trade = process_signal_action(sig_trade)
    assert res_trade["action"] == "paper_trade"
    assert res_trade["signal_type"] == "sell"

def test_is_safe_to_trade_gap():
    df = pd.DataFrame({
        "open": [100.0, 105.0],
        "close": [100.0, 105.0]
    })
    # gap is 5.0 on a 100.0 price = 5.0%
    res = is_safe_to_trade_gap(df, max_gap_pct=2.0)
    assert res["safe"] is False
    assert np.isclose(res["gap_pct"], 5.0)

    res2 = is_safe_to_trade_gap(df, max_gap_pct=6.0)
    assert res2["safe"] is True

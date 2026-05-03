import json

from quant_engine.research.lifecycle import (
    can_transition,
    generate_postmortem,
    generate_risk_cards,
    get_next_logical_step,
)


def test_can_transition():
    # Valid
    assert can_transition("draft", "pretest") is True
    assert can_transition("optimized", "wfa_passed") is True
    assert can_transition("paper_watching", "retired") is True
    assert can_transition("retired", "draft") is True # Resurrect

    # Invalid
    assert can_transition("draft", "optimized") is False # Skipped step
    assert can_transition("monte_carlo_passed", "draft") is False
    assert can_transition("invalid", "pretest") is False
    assert can_transition("draft", "invalid") is False

def test_get_next_logical_step():
    assert get_next_logical_step("draft") == "pretest"
    assert get_next_logical_step("pretest") == "optimized"
    assert get_next_logical_step("paper_watching") == "retired"
    assert get_next_logical_step("retired") == "none"

def test_generate_risk_cards():
    metrics = {
        "data_gap_pct": 2.0,            # Triggers data risk
        "param_count": 6,               # Triggers overfit risk
        "avg_volume": 50000,            # Triggers liquidity risk
        "has_slippage_assumptions": False, # Triggers slippage risk
        "market": "BIST",
        "allows_short": True,           # Triggers short sim risk
        "intrabar_fill": True           # Triggers repaint risk
    }
    cards = generate_risk_cards(metrics)
    assert len(cards) == 6
    types = [c["type"] for c in cards]
    assert "data_risk" in types
    assert "overfit_risk" in types
    assert "liquidity_risk" in types
    assert "slippage_risk" in types
    assert "short_sim_risk" in types
    assert "repaint_risk" in types

    metrics_clean = {
        "data_gap_pct": 0.0,
        "bar_count": 1000,
        "param_count": 2,
        "wfa_passed": True,
        "avg_volume": 500000,
        "has_slippage_assumptions": True,
        "market": "CRYPTO",
        "allows_short": True,
        "intrabar_fill": False,
        "uses_future_data": False
    }
    cards_clean = generate_risk_cards(metrics_clean)
    assert len(cards_clean) == 0

def test_generate_postmortem():
    res = generate_postmortem(
        strategy_id="ST_123",
        reason="Consistent drawdown in paper trading",
        lesson="Don't trust backtests without slippage on BIST.",
        metrics_summary={"pnl": -5.0},
        tags=["overfit", "bist"]
    )

    assert res["strategy_id"] == "ST_123"
    assert res["reason"] == "Consistent drawdown in paper trading"
    assert res["tags"] == ["overfit", "bist"]
    assert "timestamp" in res

    # Assert JSON serializable
    json.dumps(res)

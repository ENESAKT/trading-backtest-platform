import pytest
from datetime import datetime, timezone
import json

from quant_engine.strategy import get_strategy_preset, preset_to_strategy_spec, export_strategy_pack, import_strategy_pack
from quant_engine.backtest.quality import compute_quality_score
from quant_engine.research import run_walk_forward_analysis, run_monte_carlo, find_stable_region, scan_market, portfolio_metrics, generate_preflight_checklist, get_next_logical_step
import pandas as pd

def test_full_b1_b13_integration_chain():
    # 1. Catalog preset
    preset = get_strategy_preset("momentum_rsi_macd")
    assert preset is not None
    
    # 2. Spec validation
    spec = preset_to_strategy_spec("momentum_rsi_macd")
    assert spec["name"] == "RSI MACD Momentum"
    
    class MockResult:
        def __init__(self):
            self.symbol = "BTCUSDT"
            self.interval = "1d"
            self.strategy_id = "momentum_rsi_macd"
            self.params = {}
            self.capital = 100000.0
            self.lookback_bars = 100
            self.metrics = type("MockMetrics", (), {
                "final_equity": 110000.0,
                "total_return_pct": 10.0,
                "max_drawdown_pct": 5.0,
                "total_trades": 10,
                "total_commission": 50.0,
                "sharpe_ratio": 1.5,
                "win_rate": 60.0,
                "has_open_position": False
            })()
            self.equity_curve = []
            self.trades = [{"pnl_pct": 2.0}, {"pnl_pct": -1.0}]
            self.signals = []
            
    result = MockResult()
    
    # 3. Quality score
    metrics_dict = {
        "total_trades": result.metrics.total_trades,
        "days_tested": 100,
        "max_drawdown_pct": result.metrics.max_drawdown_pct,
        "param_count": len(result.params) if result.params else 1,
    }
    q_score = compute_quality_score(metrics_dict)
    assert q_score["score"] >= 0
    
    # 4. WFA (Mocked input)
    data = pd.DataFrame({"close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    wfa_report = run_walk_forward_analysis(
        data,
        [{"param1": 1}],
        lambda p, d: 1.0,
        lambda p, d: 1.0,
        in_sample_bars=4,
        out_of_sample_bars=2,
        step_bars=2,
    )
    assert wfa_report.passed is not None
    
    # 5. Monte Carlo
    pnl_series = [t["pnl_pct"] for t in result.trades]
    mc_report = run_monte_carlo(pnl_series, n_simulations=10)
    assert mc_report.probability_of_loss >= 0
    
    # 6. Optimization v2
    opt_report = find_stable_region([{"params": {"p1": 1, "p2": 2}, "net_profit": 10}], "p1", "p2")
    assert opt_report.get("best_p1") is not None
    
    # 7. Scanner v3
    scan_report = scan_market({"BTCUSDT": data})
    assert isinstance(scan_report, list)
    
    # 8. Portfolio Lab
    port_report = portfolio_metrics(pd.Series([100, 110, 120]))
    assert port_report["total_return_pct"] is not None
    
    # 9. Paper Ops
    paper_preflight = generate_preflight_checklist({"has_real_data": True, "bar_count": 500, "wfa_passed": True, "monte_carlo_passed": True})
    assert paper_preflight.get("ready_to_start") is not None
    
    # 10. Lifecycle
    transition = get_next_logical_step("optimized")
    assert transition == "wfa_passed"
    
    # 11. Pack export/import
    exported = export_strategy_pack(spec, description=transition)
    
    # Check JSON serializable
    json.dumps(exported)
    
    imported = import_strategy_pack(exported)
    assert imported["strategy_spec"]["name"] == spec["name"]

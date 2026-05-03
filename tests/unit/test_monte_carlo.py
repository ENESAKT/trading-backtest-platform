import pytest
import numpy as np
from quant_engine.research.monte_carlo import run_monte_carlo

def test_monte_carlo_empty_pnl():
    report = run_monte_carlo([])
    assert len(report.warnings) == 1
    assert report.warnings[0] == "Empty PnL series provided."
    assert report.simulations == []

def test_monte_carlo_deterministic_seed():
    pnl = [100.0, -50.0, 200.0, -100.0, 50.0]
    report1 = run_monte_carlo(pnl, seed=42, n_simulations=10)
    report2 = run_monte_carlo(pnl, seed=42, n_simulations=10)
    
    assert report1.median_final_equity == report2.median_final_equity
    assert report1.p05_final_equity == report2.p05_final_equity
    assert report1.p95_final_equity == report2.p95_final_equity
    assert report1.probability_of_loss == report2.probability_of_loss
    assert report1.median_max_drawdown_pct == report2.median_max_drawdown_pct
    assert report1.p95_max_drawdown_pct == report2.p95_max_drawdown_pct
    assert len(report1.simulations) == 10

def test_monte_carlo_bootstrap_method():
    pnl = [50.0] * 5  # All trades are profitable
    report = run_monte_carlo(pnl, initial_capital=1000.0, n_simulations=5, method='bootstrap')
    assert report.median_final_equity == 1250.0  # 1000 + 50*5
    assert report.probability_of_loss == 0.0
    assert report.median_max_drawdown_pct == 0.0

def test_monte_carlo_permutation_method():
    pnl = [100.0, -50.0]  # Sum is 50
    report = run_monte_carlo(pnl, initial_capital=1000.0, n_simulations=2, method='permutation')
    # Permutation just reorders, final equity is always the same
    assert report.median_final_equity == 1050.0
    assert report.p05_final_equity == 1050.0
    assert report.p95_final_equity == 1050.0

def test_monte_carlo_probability_of_loss():
    pnl = [-100.0, -100.0]  # Always lose
    report = run_monte_carlo(pnl, initial_capital=1000.0, n_simulations=10, method='bootstrap')
    assert report.probability_of_loss == 1.0

def test_monte_carlo_risk_pct():
    pnl = [0.1, -0.05]  # e.g., returns
    # With 1000 capital, if we risk 50% on each trade
    report = run_monte_carlo(pnl, initial_capital=1000.0, n_simulations=2, method='permutation', risk_pct=0.5)
    # The first pnl is either 0.1 or -0.05
    # If 0.1 first: equity1 = 1000 + 1000*0.5*0.1 = 1050. equity2 = 1050 + 1050*0.5*-0.05 = 1050 - 26.25 = 1023.75
    # If -0.05 first: equity1 = 1000 + 1000*0.5*-0.05 = 975. equity2 = 975 + 975*0.5*0.1 = 975 + 48.75 = 1023.75
    # Final equity is the same in both cases due to the nature of product of multipliers?
    # Wait: multiplier = (1 + risk_pct * pnl). (1 + 0.5*0.1) * (1 + 0.5*-0.05) = 1.05 * 0.975 = 1.02375.
    # 1000 * 1.02375 = 1023.75
    assert report.median_final_equity == 1023.75

def test_monte_carlo_drawdown():
    # If we go 1000 -> 900 -> 1000
    pnl = [-100.0, 100.0]
    report = run_monte_carlo(pnl, initial_capital=1000.0, n_simulations=1, method='permutation', seed=42)
    # Max drawdown is calculated from peak.
    # If -100 first: peak = 1000, current = 900. DD = 100/1000 = 10%. Then 1000, peak = 1000. Max DD = 10%.
    # If 100 first: peak = 1100. current = 1000. DD = 100/1100 = 9.09%. Max DD = 9.09%.
    # Seed 42 might give one of these.
    # We can check it's one of them.
    assert np.isclose(report.median_max_drawdown_pct, 10.0) or np.isclose(report.median_max_drawdown_pct, 100/11.0)

import numpy as np
import pandas as pd
import pytest

from quant_engine.research.portfolio_lab import (
    check_risk_limits,
    combine_equity_curves,
    correlation_matrix,
    portfolio_metrics,
)


@pytest.fixture
def sample_curves():
    dates = pd.date_range('2023-01-01', periods=5)
    # Return series: 0, 10%, -5%, 5%, 10%
    # Curve 1
    c1 = pd.Series([100, 110, 104.5, 109.725, 120.6975], index=dates)
    # Return series: 0, -5%, 10%, -2%, 5%
    # Curve 2
    c2 = pd.Series([100, 95, 104.5, 102.41, 107.5305], index=dates)
    return [c1, c2]

def test_combine_equity_curves(sample_curves):
    c1, c2 = sample_curves
    combined = combine_equity_curves([c1, c2]) # weights=[0.5, 0.5]

    assert len(combined) == 5
    assert combined.iloc[0] == 1.0 # Base 1.0

    # 1st ret: c1=0.10, c2=-0.05 => avg = 0.025. combined[1] should be 1.025
    assert np.isclose(combined.iloc[1], 1.025)

def test_combine_equity_curves_weights(sample_curves):
    c1, c2 = sample_curves
    combined = combine_equity_curves([c1, c2], weights=[0.8, 0.2])

    # 1st ret: c1=0.10, c2=-0.05 => 0.08 - 0.01 = 0.07 => combined[1] = 1.07
    assert np.isclose(combined.iloc[1], 1.07)

def test_combine_equity_curves_errors():
    with pytest.raises(ValueError):
        combine_equity_curves([])

    s1 = pd.Series([100, 110])
    with pytest.raises(ValueError):
        combine_equity_curves([s1], weights=[0.5, 0.5])

def test_correlation_matrix():
    df = pd.DataFrame({
        'A': [0.01, -0.02, 0.03, -0.01],
        'B': [0.02, -0.04, 0.06, -0.02], # Perfect pos correlation with A
        'C': [-0.01, 0.02, -0.03, 0.01]  # Perfect neg correlation with A
    })
    res = correlation_matrix(df)

    assert res['labels'] == ['A', 'B', 'C']
    mat = res['matrix']
    assert np.isclose(mat[0][1], 1.0)
    assert np.isclose(mat[0][2], -1.0)

def test_portfolio_metrics(sample_curves):
    combined = combine_equity_curves(sample_curves)
    res = portfolio_metrics(combined)

    assert 'total_return_pct' in res
    assert 'max_drawdown_pct' in res
    assert 'profit_factor' in res
    assert 'sharpe_like' in res
    assert 'worst_period_pct' in res
    assert 'monthly_returns' in res

    assert res['total_return_pct'] > 0
    assert isinstance(res['worst_period_pct'], float)

def test_check_risk_limits():
    alloc = {
        'strat_1': 5000,
        'strat_2': 6000
    }

    # All good
    warns = check_risk_limits(alloc, 10000, 20000)
    assert len(warns) == 0

    # Exceed single strategy limit
    warns = check_risk_limits(alloc, 5500, 20000)
    assert len(warns) == 1
    assert 'strat_2' in warns[0]

    # Exceed total
    warns = check_risk_limits(alloc, 10000, 10000)
    assert len(warns) == 1
    assert 'Toplam portföy riski' in warns[0]

from quant_engine.backtest.quality import compute_quality_score


def test_perfect_quality_score():
    metrics = {
        'total_trades': 150,
        'days_tested': 365,
        'max_drawdown_pct': 15.0,
        'param_count': 2,
        'num_symbols': 5,
        'intrabar_risks': 0,
        'missing_data_pct': 0.0,
        'max_win_contribution_pct': 10.0
    }
    res = compute_quality_score(metrics)
    assert res['score'] == 100
    assert len(res['warnings']) == 0

def test_poor_quality_score():
    metrics = {
        'total_trades': 10,       # -20
        'days_tested': 30,        # -15
        'max_drawdown_pct': 60.0, # -30
        'param_count': 6,         # -15
        'num_symbols': 1,         # -5
        'intrabar_risks': 2,      # -10
        'missing_data_pct': 10.0, # -20
        'max_win_contribution_pct': 50.0 # -15
    }
    # Total deduction: 20+15+30+15+5+10+20+15 = 130 -> score 0
    res = compute_quality_score(metrics)
    assert res['score'] == 0
    assert len(res['warnings']) == 8

    severities = [w['severity'] for w in res['warnings']]
    assert severities.count('high') == 6
    assert severities.count('medium') == 1
    assert severities.count('low') == 1

def test_medium_quality_score():
    metrics = {
        'total_trades': 50,       # -5
        'days_tested': 120,       # -5
        'max_drawdown_pct': 35.0, # -10
        'param_count': 4,         # -5
        'num_symbols': 10,        # 0
        'intrabar_risks': 0,      # 0
        'missing_data_pct': 2.0,  # -5
        'max_win_contribution_pct': 25.0 # -5
    }
    # Total deduction: 5+5+10+5+5+5 = 35 -> score 65
    res = compute_quality_score(metrics)
    assert res['score'] == 65
    assert len(res['warnings']) == 6

def test_empty_metrics():
    # Tests defaults
    res = compute_quality_score({})
    assert res['score'] < 100
    assert any("işlem sayısı" in w['message'].lower() for w in res['warnings'])

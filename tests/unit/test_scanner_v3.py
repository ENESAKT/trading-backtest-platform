
import numpy as np
import pandas as pd
import pytest

from quant_engine.research.scanner_v3 import (
    filter_data_status,
    filter_liquidity,
    filter_price_ma_distance,
    filter_recent_signal,
    filter_rsi_zone,
    filter_volume_above_avg,
    scan_market,
)


@pytest.fixture
def mock_universe():
    dates = pd.date_range('2023-01-01', periods=10)
    df_a = pd.DataFrame({
        'close': np.linspace(100, 110, 10),
        'volume': np.full(10, 500000),
        'signal': [0]*9 + [1],
        'ma': np.linspace(95, 105, 10),
        'rsi': np.full(10, 50),
        'avg_volume': np.full(10, 400000),
        'fast_ma': np.linspace(101, 111, 10),
        'slow_ma': np.linspace(99, 109, 10)
    }, index=dates)

    df_b = pd.DataFrame({
        'close': np.linspace(50, 40, 10),
        'volume': np.full(10, 10000), # Low volume
        'signal': [0]*10,
        'ma': np.linspace(55, 45, 10),
        'rsi': np.full(10, 20),
        'avg_volume': np.full(10, 20000),
        'fast_ma': np.linspace(49, 39, 10),
        'slow_ma': np.linspace(51, 41, 10)
    }, index=dates)

    df_c = pd.DataFrame() # Empty

    return {'A': df_a, 'B': df_b, 'C': df_c}

def test_scan_market_basic(mock_universe):
    results = scan_market(mock_universe)
    assert len(results) == 3

    # Check A
    res_a = next(r for r in results if r['symbol'] == 'A')
    assert res_a['last_price'] == 110.0
    assert res_a['data_status'] == 'ready'
    assert not res_a['liquidity_warning']

    # Check C
    res_c = next(r for r in results if r['symbol'] == 'C')
    assert res_c['last_price'] is None
    assert res_c['data_status'] == 'empty'

def test_scanner_with_filters(mock_universe):
    filters = [
        lambda df: filter_recent_signal(df, 'signal', 3),
        lambda df: filter_data_status(df, min_bars=5)
    ]

    results = scan_market(mock_universe, filters=filters)
    # B has no signal, C is empty (handled internally).
    # C will be returned as empty. B will be skipped because of filter_recent_signal!
    symbols = [r['symbol'] for r in results]
    assert 'A' in symbols
    assert 'B' not in symbols # Skipped
    assert 'C' in symbols # Empty dfs are always returned with empty status

def test_scanner_liquidity_warning(mock_universe):
    filters = [
        lambda df: filter_liquidity(df, min_volume=100000)
    ]
    results = scan_market(mock_universe, filters=filters)
    res_b = next(r for r in results if r['symbol'] == 'B')
    assert res_b['liquidity_warning'] is True

def test_filter_helpers():
    df = pd.DataFrame({
        'close': [100, 105],
        'ma': [95, 100],
        'rsi': [40, 45],
        'volume': [1000, 2000],
        'avg_volume': [1500, 1500]
    })

    # price ma dist
    assert filter_price_ma_distance(df, 'ma', max_pct_distance=6.0)['passed'] # (105-100)/100 = 5%
    assert not filter_price_ma_distance(df, 'ma', max_pct_distance=4.0)['passed']

    # rsi zone
    assert filter_rsi_zone(df, min_val=40, max_val=50)['passed']
    assert not filter_rsi_zone(df, min_val=50, max_val=60)['passed']

    # volume above avg
    assert filter_volume_above_avg(df)['passed']

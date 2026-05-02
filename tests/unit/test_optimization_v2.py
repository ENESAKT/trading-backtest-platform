import pytest

from quant_engine.research.optimization_v2 import find_stable_region, generate_heatmap_data


@pytest.fixture
def sample_grid_results():
    return [
        {'params': {'p1': 10, 'p2': 100}, 'net_profit': 10.0},
        {'params': {'p1': 10, 'p2': 200}, 'net_profit': 20.0},
        {'params': {'p1': 10, 'p2': 300}, 'net_profit': 15.0},

        {'params': {'p1': 20, 'p2': 100}, 'net_profit': 30.0},
        {'params': {'p1': 20, 'p2': 200}, 'net_profit': 100.0}, # Spike, unstable
        {'params': {'p1': 20, 'p2': 300}, 'net_profit': 25.0},

        {'params': {'p1': 30, 'p2': 100}, 'net_profit': 80.0}, # Stable region start
        {'params': {'p1': 30, 'p2': 200}, 'net_profit': 85.0}, # Stable region middle
        {'params': {'p1': 30, 'p2': 300}, 'net_profit': 82.0}, # Stable region end

        {'params': {'p1': 40, 'p2': 100}, 'net_profit': 75.0},
        {'params': {'p1': 40, 'p2': 200}, 'net_profit': 80.0},
        {'params': {'p1': 40, 'p2': 300}, 'net_profit': 78.0},
    ]

def test_generate_heatmap_data(sample_grid_results):
    hm = generate_heatmap_data(sample_grid_results, 'p1', 'p2')
    assert hm['x_axis'] == [10, 20, 30, 40]
    assert hm['y_axis'] == [100, 200, 300]

    z = hm['z_matrix']
    assert len(z) == 3 # 3 y values
    assert len(z[0]) == 4 # 4 x values

    # Check y=200, x=20 (spike)
    # y_axis index for 200 is 1. x_axis index for 20 is 1.
    assert z[1][1] == 100.0

def test_find_stable_region(sample_grid_results):
    res = find_stable_region(sample_grid_results, 'p1', 'p2', threshold=0.7)

    # Global max is 100 at (p1=20, p2=200)
    # But its neighbors are 30, 25, 20, 85, etc. Average is much lower.
    # The stable region is around (p1=30, p2=200) where neighbors are 80, 82, 75, 80, 100, etc.

    assert res['best_p1'] == 40
    assert res['best_p2'] == 300
    assert res['global_max'] == 100.0
    assert res['metric_value'] == 78.0

def test_find_stable_region_empty():
    assert find_stable_region([], 'p1', 'p2') == {}

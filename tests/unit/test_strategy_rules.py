import numpy as np
import pandas as pd
import pytest

from quant_engine.strategy.rules import (
    above,
    bars_since,
    below,
    cross_down,
    cross_up,
    distance_pct,
    falling,
    fixed_stop_pct,
    rising,
    slope,
    take_profit_pct,
    time_stop_bars,
    trailing_stop_pct,
    volume_above_avg,
)


def test_cross_up():
    s1 = pd.Series([10, 11, 12, 13, 14])
    s2 = pd.Series([12, 12, 12, 12, 12])
    res = cross_up(s1, s2)
    assert not res.iloc[0]
    assert not res.iloc[1]
    assert not res.iloc[2]
    assert res.iloc[3] # 13 > 12, prev 12 <= 12
    assert not res.iloc[4]

def test_cross_down():
    s1 = pd.Series([14, 13, 12, 11, 10])
    s2 = pd.Series([12, 12, 12, 12, 12])
    res = cross_down(s1, s2)
    assert not res.iloc[2]
    assert res.iloc[3] # 11 < 12, prev 12 >= 12
    assert not res.iloc[4]

def test_above_below():
    s1 = pd.Series([10, 15, 20])
    s2 = pd.Series([15, 15, 15])

    ab = above(s1, s2)
    assert not ab.iloc[0]
    assert not ab.iloc[1]
    assert ab.iloc[2]

    be = below(s1, s2)
    assert be.iloc[0]
    assert not be.iloc[1]
    assert not be.iloc[2]

def test_bars_since():
    cond = pd.Series([False, True, False, False, True, False])
    res = bars_since(cond)
    assert np.isnan(res.iloc[0])
    assert res.iloc[1] == 0
    assert res.iloc[2] == 1
    assert res.iloc[3] == 2
    assert res.iloc[4] == 0
    assert res.iloc[5] == 1

def test_distance_pct():
    s1 = pd.Series([110, 90])
    s2 = pd.Series([100, 100])
    res = distance_pct(s1, s2)
    assert np.isclose(res.iloc[0], 10.0)
    assert np.isclose(res.iloc[1], -10.0)

def test_slope():
    s = pd.Series([10, 11, 12, 13, 14])
    res = slope(s, period=3)
    assert np.isnan(res.iloc[1])
    assert np.isclose(res.iloc[2], 1.0) # Slope of [10, 11, 12] is 1.0

    with pytest.raises(ValueError):
        slope(s, 1)

def test_rising_falling():
    s = pd.Series([10, 11, 12, 10, 9, 8])
    r = rising(s, period=2)
    assert r.iloc[2] # 11>10, 12>11
    assert not r.iloc[3]

    f = falling(s, period=2)
    assert not f.iloc[3]
    assert f.iloc[5] # 9<10, 8<9

    with pytest.raises(ValueError):
        rising(s, 0)
    with pytest.raises(ValueError):
        falling(s, 0)

def test_volume_above_avg():
    vol = pd.Series([100, 100, 100, 150])
    res = volume_above_avg(vol, period=3)
    assert not res.iloc[2]
    assert res.iloc[3]

    with pytest.raises(ValueError):
        volume_above_avg(vol, 0)

def test_risk_templates():
    assert fixed_stop_pct(2.5) == {"type": "fixed_pct", "value": 2.5}
    with pytest.raises(ValueError):
        fixed_stop_pct(0)

    assert take_profit_pct(5.0) == {"type": "take_profit_pct", "value": 5.0}
    with pytest.raises(ValueError):
        take_profit_pct(-1)

    assert trailing_stop_pct(1.5) == {"type": "trailing_pct", "value": 1.5}
    assert trailing_stop_pct(1.5, 2.0) == {"type": "trailing_pct", "value": 1.5, "activation_value": 2.0}
    with pytest.raises(ValueError):
        trailing_stop_pct(-1)
    with pytest.raises(ValueError):
        trailing_stop_pct(1.5, 0)

    assert time_stop_bars(10) == {"type": "time_stop_bars", "value": 10}
    with pytest.raises(ValueError):
        time_stop_bars(0)

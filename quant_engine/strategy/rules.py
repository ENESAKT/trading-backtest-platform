import numpy as np
import pandas as pd


def cross_up(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Returns True where s1 crosses above s2."""
    if isinstance(s2, (int, float)):
        s2 = pd.Series(s2, index=s1.index)
    return (s1 > s2) & (s1.shift(1) <= s2.shift(1))

def cross_down(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Returns True where s1 crosses below s2."""
    if isinstance(s2, (int, float)):
        s2 = pd.Series(s2, index=s1.index)
    return (s1 < s2) & (s1.shift(1) >= s2.shift(1))

def above(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Returns True where s1 is strictly greater than s2."""
    return s1 > s2

def below(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Returns True where s1 is strictly less than s2."""
    return s1 < s2

def bars_since(condition: pd.Series) -> pd.Series:
    """
    Returns the number of bars since the condition was True.
    If the condition is True on the current bar, returns 0.
    If the condition has never been True, returns NaN.
    """
    result = pd.Series(np.nan, index=condition.index)

    # We can calculate this using cumulative sums and groupbys, but a simpler
    # vectorized way is to find indices.
    # A common pandas trick for bars_since:
    # Find the index of the current group
    # We need to calculate distance to the last True.
    # Create a series of row indices
    idx = pd.Series(np.arange(len(condition)), index=condition.index)

    # For rows where condition is True, keep the index, else NaN
    true_idx = idx.where(condition)

    # Forward fill the true indices to get the index of the last True
    last_true_idx = true_idx.ffill()

    # The number of bars since is current index minus last True index
    result = idx - last_true_idx

    return result

def distance_pct(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Returns the percentage distance of s1 relative to s2."""
    return ((s1 - s2) / s2) * 100

def slope(series: pd.Series, period: int = 5) -> pd.Series:
    """
    Returns the slope of the linear regression line over 'period' bars.
    Using vectorized least squares.
    """
    if period < 2:
        raise ValueError("Slope period must be at least 2")

    x = np.arange(period)
    x_mean = x.mean()
    x_diff = x - x_mean
    sum_x_diff_sq = np.sum(x_diff**2)

    def calc_slope(y):
        if len(y) < period or np.isnan(y).any():
            return np.nan
        y_mean = np.mean(y)
        return np.sum(x_diff * (y - y_mean)) / sum_x_diff_sq

    return series.rolling(window=period, min_periods=period).apply(calc_slope, raw=True)

def rising(series: pd.Series, period: int = 3) -> pd.Series:
    """
    Returns True if the series has been strictly rising for 'period' bars.
    (i.e. each bar is > previous bar)
    """
    if period < 1:
        raise ValueError("Rising period must be at least 1")
    diff = series.diff()
    is_rising = diff > 0
    return is_rising.rolling(window=period, min_periods=period).sum() == period

def falling(series: pd.Series, period: int = 3) -> pd.Series:
    """
    Returns True if the series has been strictly falling for 'period' bars.
    """
    if period < 1:
        raise ValueError("Falling period must be at least 1")
    diff = series.diff()
    is_falling = diff < 0
    return is_falling.rolling(window=period, min_periods=period).sum() == period

def volume_above_avg(volume: pd.Series, period: int = 20) -> pd.Series:
    """Returns True if current volume is strictly greater than its simple moving average."""
    if period < 1:
        raise ValueError("Period must be at least 1")
    avg_vol = volume.rolling(window=period, min_periods=period).mean()
    return volume > avg_vol

# Risk Template Helpers (JSON serializable models for StrategySpec)

def fixed_stop_pct(pct: float) -> dict:
    """Risk template for fixed stop loss percentage."""
    if pct <= 0:
        raise ValueError("Stop loss percentage must be > 0")
    return {"type": "fixed_pct", "value": pct}

def take_profit_pct(pct: float) -> dict:
    """Risk template for take profit percentage."""
    if pct <= 0:
        raise ValueError("Take profit percentage must be > 0")
    return {"type": "take_profit_pct", "value": pct}

def trailing_stop_pct(pct: float, activation_pct: float = None) -> dict:
    """Risk template for trailing stop percentage."""
    if pct <= 0:
        raise ValueError("Trailing stop percentage must be > 0")
    res = {"type": "trailing_pct", "value": pct}
    if activation_pct is not None:
        if activation_pct <= 0:
            raise ValueError("Activation percentage must be > 0")
        res["activation_value"] = activation_pct
    return res

def time_stop_bars(bars: int) -> dict:
    """Risk template for time-based stop (exit after N bars)."""
    if bars < 1:
        raise ValueError("Time stop bars must be at least 1")
    return {"type": "time_stop_bars", "value": bars}

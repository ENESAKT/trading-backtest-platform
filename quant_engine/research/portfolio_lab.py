import numpy as np
import pandas as pd


def combine_equity_curves(curves: list[pd.Series], weights: list[float] = None) -> pd.Series:
    """
    Combines multiple equity curves into a single portfolio equity curve.
    
    Args:
        curves: List of pd.Series representing equity curves (must have datetime index).
        weights: List of weights for each curve. If None, equal weighting is applied.
        
    Returns:
        pd.Series: Combined equity curve.
    """
    if not curves:
        raise ValueError("No curves provided")

    if weights is None:
        weights = [1.0 / len(curves)] * len(curves)

    if len(curves) != len(weights):
        raise ValueError("Number of curves must match number of weights")

    # Convert all to daily returns to combine properly
    # If they are equity values (e.g. 10000, 10500, etc), pct_change gives returns
    returns = []
    for curve in curves:
        # Fill missing with 0 return
        ret = curve.pct_change().fillna(0)
        returns.append(ret)

    # Combine returns into a dataframe
    df_ret = pd.concat(returns, axis=1).fillna(0)

    # Weighted average of returns
    port_ret = df_ret.dot(weights)

    # Reconstruct equity curve (base 1.0)
    combined_equity = (1 + port_ret).cumprod()

    return combined_equity

def correlation_matrix(returns_df: pd.DataFrame) -> dict:
    """
    Computes the correlation matrix for a dataframe of returns.
    
    Returns:
        dict: JSON serializable dict with 'labels' and 'matrix'
    """
    if returns_df.empty:
        return {"labels": [], "matrix": []}

    corr = returns_df.corr().fillna(0)
    return {
        "labels": list(corr.columns),
        "matrix": corr.values.tolist()
    }

def portfolio_metrics(combined_curve: pd.Series, risk_free_rate: float = 0.0) -> dict:
    """
    Computes key portfolio metrics from a combined equity curve.
    """
    if combined_curve.empty or len(combined_curve) < 2:
        return {
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "profit_factor": 0.0,
            "sharpe_like": 0.0,
            "worst_period_pct": 0.0,
            "monthly_returns": {}
        }

    total_return = (combined_curve.iloc[-1] / combined_curve.iloc[0]) - 1

    # Drawdown
    running_max = combined_curve.cummax()
    drawdown = (combined_curve - running_max) / running_max
    max_dd = abs(drawdown.min())

    # Returns
    rets = combined_curve.pct_change().dropna()

    # Sharpe-like (annualized)
    # Assuming daily data
    mean_ret = rets.mean()
    std_ret = rets.std()
    sharpe = 0.0
    if std_ret > 0:
        sharpe = ((mean_ret - (risk_free_rate/252)) / std_ret) * np.sqrt(252)

    # Profit factor estimation (sum of positive returns / sum of negative returns)
    pos_rets = rets[rets > 0].sum()
    neg_rets = abs(rets[rets < 0].sum())
    pf = pos_rets / neg_rets if neg_rets > 0 else float('inf')
    if pd.isna(pf):
        pf = 0.0

    # Worst period (worst daily return)
    worst = rets.min() if not rets.empty else 0.0

    # Monthly returns
    monthly_returns = {}
    if hasattr(combined_curve.index, 'month'):
        # Resample to monthly and get last value of each month
        try:
            monthly = combined_curve.resample('ME').last()
            m_rets = monthly.pct_change().dropna()
            for date, val in m_rets.items():
                k = f"{date.year}-{date.month:02d}"
                monthly_returns[k] = round(val * 100, 2)
        except Exception:
            pass

    return {
        "total_return_pct": round(total_return * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "profit_factor": round(float(pf), 2),
        "sharpe_like": round(float(sharpe), 2),
        "worst_period_pct": round(worst * 100, 2),
        "monthly_returns": monthly_returns
    }

def check_risk_limits(allocations: dict, max_capital_per_strategy: float, max_total_exposure: float) -> list:
    """
    Checks if strategy allocations exceed risk limits.
    
    Args:
        allocations: dict mapping strategy_id -> capital_allocated
        max_capital_per_strategy: max allowed capital for a single strategy
        max_total_exposure: max allowed capital across all strategies
        
    Returns:
        List of warning strings. Empty list if all good.
    """
    warnings = []
    total = 0.0

    for st_id, cap in allocations.items():
        if cap > max_capital_per_strategy:
            warnings.append(f"Strateji '{st_id}' için ayrılan sermaye ({cap}) limitin ({max_capital_per_strategy}) üzerinde.")
        total += cap

    if total > max_total_exposure:
        warnings.append(f"Toplam portföy riski ({total}) izin verilen maksimum limitin ({max_total_exposure}) üzerinde.")

    return warnings

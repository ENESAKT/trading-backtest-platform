import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class MonteCarloReport:
    median_final_equity: float = 0.0
    p05_final_equity: float = 0.0
    p95_final_equity: float = 0.0
    probability_of_loss: float = 0.0
    median_max_drawdown_pct: float = 0.0
    p95_max_drawdown_pct: float = 0.0
    simulations: List[List[float]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def run_monte_carlo(
    pnl_series: List[float],
    initial_capital: float = 10000.0,
    n_simulations: int = 1000,
    method: str = 'bootstrap',
    seed: Optional[int] = None,
    risk_pct: Optional[float] = None,
) -> MonteCarloReport:
    """
    Run Monte Carlo simulation on a series of PnL values.
    
    :param pnl_series: List of trade PnL values.
    :param initial_capital: Starting capital for the simulation.
    :param n_simulations: Number of simulation iterations.
    :param method: 'bootstrap' (with replacement) or 'permutation' (without replacement).
    :param seed: Random seed for reproducibility.
    :param risk_pct: If provided, pnl_series is treated as return multipliers and scaled by (current_equity * risk_pct).
                     If None, pnl_series is treated as absolute currency PnL.
    :return: MonteCarloReport containing simulation metrics.
    """
    if not pnl_series:
        return MonteCarloReport(warnings=["Empty PnL series provided."])
        
    rng = np.random.default_rng(seed)
    pnl_array = np.array(pnl_series, dtype=float)
    n_trades = len(pnl_array)
    
    simulations = []
    final_equities = []
    max_drawdowns_pct = []
    
    warnings = []
    if method not in ('bootstrap', 'permutation'):
        warnings.append(f"Unknown method '{method}', falling back to 'bootstrap'.")
        method = 'bootstrap'
        
    for _ in range(n_simulations):
        if method == 'permutation':
            sample_pnl = rng.permutation(pnl_array)
        else:
            sample_pnl = rng.choice(pnl_array, size=n_trades, replace=True)
            
        equity_curve = [initial_capital]
        current_equity = initial_capital
        peak_equity = initial_capital
        max_dd_pct = 0.0
        
        for pnl in sample_pnl:
            if risk_pct is not None:
                trade_pnl = current_equity * risk_pct * pnl
            else:
                trade_pnl = pnl
                
            current_equity += trade_pnl
            equity_curve.append(current_equity)
            
            if current_equity > peak_equity:
                peak_equity = current_equity
                
            if peak_equity > 0:
                dd_pct = (peak_equity - current_equity) / peak_equity * 100.0
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                    
        simulations.append(equity_curve)
        final_equities.append(current_equity)
        max_drawdowns_pct.append(max_dd_pct)
        
    final_equities_arr = np.array(final_equities)
    max_drawdowns_pct_arr = np.array(max_drawdowns_pct)
    
    return MonteCarloReport(
        median_final_equity=float(np.median(final_equities_arr)),
        p05_final_equity=float(np.percentile(final_equities_arr, 5)),
        p95_final_equity=float(np.percentile(final_equities_arr, 95)),
        probability_of_loss=float(np.mean(final_equities_arr < initial_capital)),
        median_max_drawdown_pct=float(np.median(max_drawdowns_pct_arr)),
        p95_max_drawdown_pct=float(np.percentile(max_drawdowns_pct_arr, 95)),
        simulations=simulations,
        warnings=warnings
    )

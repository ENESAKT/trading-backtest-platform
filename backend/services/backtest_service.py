"""BacktestService — thin orchestration wrapper around backend.backtest.runner."""

from __future__ import annotations

from backend.api.schemas import BacktestRequest, BacktestResponse
from backend.backtest.runner import run_backtest
from quant_engine.data.ohlcv_cache import OHLCVCache


class BacktestService:
    """Orchestrates backtest execution via quant_engine.

    Delegates to ``run_backtest`` in backend.backtest.runner.  This class
    exists as a service-layer seam so routers outside ``main.py`` (tests,
    CLI, scheduled workers) can call backtest logic without importing the
    full FastAPI application.
    """

    def __init__(self, cache: OHLCVCache | None = None) -> None:
        self._cache = cache or OHLCVCache()

    async def run(self, req: BacktestRequest) -> BacktestResponse:
        """Run backtest for *req* and return structured metrics."""
        result = run_backtest(
            cache=self._cache,
            symbol=req.symbol,
            interval=req.timeframe,
            strategy_id=req.strategy,
            params=req.params,
            start_date=str(req.start),
            end_date=str(req.end),
        )
        metrics = result.get("metrics", {})
        return BacktestResponse(
            strategy=req.strategy,
            symbol=req.symbol,
            sharpe=metrics.get("sharpe"),
            sortino=metrics.get("sortino"),
            max_dd=metrics.get("max_drawdown"),
            total_trades=metrics.get("total_trades"),
            win_rate=metrics.get("win_rate"),
            period_start=req.start,
            period_end=req.end,
        )

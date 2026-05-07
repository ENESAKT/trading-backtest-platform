from backend.api.schemas import BacktestRequest, BacktestResponse


class BacktestService:
    """Orchestrates backtest execution via quant_engine."""

    async def run(self, req: BacktestRequest) -> BacktestResponse:
        raise NotImplementedError

from pydantic import BaseModel
from datetime import date


class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str = "1d"
    start: date
    end: date
    params: dict = {}


class BacktestResponse(BaseModel):
    strategy: str
    symbol: str
    sharpe: float | None
    sortino: float | None
    max_dd: float | None
    total_trades: int | None
    win_rate: float | None
    period_start: date
    period_end: date

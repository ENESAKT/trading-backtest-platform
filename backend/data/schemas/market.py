from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MarketBar(BaseModel):
    market: str
    symbol: str
    instrument_type: str
    timeframe: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "provider"
    source_timeframe: str = ""
    is_derived: bool = False
    quality_status: str = "ok"
    ingest_job_id: Optional[str] = None
    ingested_at: Optional[datetime] = None

class BarResponseMetadata(BaseModel):
    source: str
    is_real: bool
    is_derived: bool
    source_timeframe: str
    quality_status: str
    coverage_pct: float

class CandleResponse(BaseModel):
    bars: List[Dict[str, Any]]
    metadata: BarResponseMetadata

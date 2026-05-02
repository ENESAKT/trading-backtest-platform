from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.data.schemas.market import MarketBar

class MarketRepository(ABC):
    @abstractmethod
    async def get_bars(
        self, 
        market: str, 
        symbol: str, 
        timeframe: str, 
        start_ts: Optional[datetime] = None, 
        end_ts: Optional[datetime] = None, 
        limit: int = 1000
    ) -> List[MarketBar]:
        pass

    @abstractmethod
    async def insert_bars(self, bars: List[MarketBar]) -> int:
        pass

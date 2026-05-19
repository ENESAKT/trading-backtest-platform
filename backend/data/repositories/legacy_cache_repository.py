import json
import os
import aiofiles
from typing import List, Optional
from datetime import datetime
from backend.data.repositories.market_repository import MarketRepository
from backend.data.schemas.market import MarketBar

class LegacyFileMarketRepository(MarketRepository):
    """
    Fallback data store okuması (Eski json dosyaları)
    Format: {"timestamp": "2024...", "open": 100, ...}
    """
    def __init__(self, base_dir: str = "data/market_data"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            
    def _get_file_path(self, market: str, symbol: str, timeframe: str) -> str:
        safe_sym = symbol.replace("/", "_")
        return os.path.join(self.base_dir, market, timeframe, f"{safe_sym}.json")

    async def get_bars(
        self, 
        market: str, 
        symbol: str, 
        timeframe: str, 
        start_ts: Optional[datetime] = None, 
        end_ts: Optional[datetime] = None, 
        limit: int = 1000
    ) -> List[MarketBar]:
        
        filepath = self._get_file_path(market, symbol, timeframe)
        if not os.path.exists(filepath):
            return []
            
        try:
            async with aiofiles.open(filepath, mode='r') as f:
                content = await f.read()
                data = json.loads(content)
        except Exception:
            return []
            
        bars = []
        for item in data:
            try:
                # Farklı formatlara karşı toleranslı olalım
                ts_str = item.get("timestamp") or item.get("datetime") or item.get("ts")
                if not ts_str:
                    continue
                    
                if isinstance(ts_str, (int, float)):
                    ts = datetime.fromtimestamp(ts_str/1000 if ts_str > 9999999999 else ts_str)
                else:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except ValueError:
                        # Eğer hala parse edemezse atla
                        continue
                
                if start_ts and ts < start_ts:
                    continue
                if end_ts and ts > end_ts:
                    continue
                    
                bars.append(MarketBar(
                    market=market,
                    symbol=symbol,
                    instrument_type="unknown",
                    timeframe=timeframe,
                    ts=ts,
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=float(item.get("volume", 0)),
                    source="legacy_file",
                ))
            except Exception:
                continue
                
        # Zaman sıralaması ve limit
        bars.sort(key=lambda x: x.ts)
        return bars[-limit:] if len(bars) > limit else bars

    async def insert_bars(self, bars: List[MarketBar]) -> int:
        pass # Bu repoya yazma yapmayacağız, sadece Legacy okuma


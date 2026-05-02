import json
import redis.asyncio as redis
import os
from typing import Optional, List
from datetime import datetime
from backend.data.schemas.market import MarketBar

class RedisMarketCache:
    def __init__(self):
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(url, decode_responses=True)
        
    def _quote_key(self, market: str, symbol: str, timeframe: str) -> str:
        return f"quote:{market}:{symbol}:{timeframe}"
        
    def _cache_key(self, symbol: str, timeframe: str, start: str, end: str, limit: int) -> str:
        return f"cache:candles:{symbol}:{timeframe}:{start}:{end}:{limit}"

    async def set_latest_quote(self, bar: MarketBar, ttl_seconds: int = 86400):
        key = self._quote_key(bar.market, bar.symbol, bar.timeframe)
        data = bar.model_dump_json()
        await self.redis.set(key, data, ex=ttl_seconds)
        # PubSub
        await self.redis.publish("ws:quotes", data)

    async def get_latest_quote(self, market: str, symbol: str, timeframe: str) -> Optional[MarketBar]:
        key = self._quote_key(market, symbol, timeframe)
        data = await self.redis.get(key)
        if data:
            return MarketBar.model_validate_json(data)
        return None
        
    async def get_cached_candles(self, symbol: str, timeframe: str, start: str, end: str, limit: int) -> Optional[List[MarketBar]]:
        key = self._cache_key(symbol, timeframe, start, end, limit)
        data = await self.redis.get(key)
        if data:
            bars_data = json.loads(data)
            return [MarketBar(**b) for b in bars_data]
        return None
        
    async def set_cached_candles(self, symbol: str, timeframe: str, start: str, end: str, limit: int, bars: List[MarketBar], ttl_seconds: int = 60):
        key = self._cache_key(symbol, timeframe, start, end, limit)
        bars_data = [b.model_dump() for b in bars]
        # ts'leri str'ye çevir ki json parse olabilesin
        for b in bars_data:
            if isinstance(b['ts'], datetime):
                b['ts'] = b['ts'].isoformat()
            if isinstance(b['ingested_at'], datetime):
                b['ingested_at'] = b['ingested_at'].isoformat()
        
        await self.redis.set(key, json.dumps(bars_data), ex=ttl_seconds)
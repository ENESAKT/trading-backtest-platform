import clickhouse_connect
from typing import List, Optional
from datetime import datetime
import os
from backend.data.repositories.market_repository import MarketRepository
from backend.data.schemas.market import MarketBar

class ClickHouseMarketRepository(MarketRepository):
    def __init__(self, host: str = "localhost", port: int = 8123, username: str = "default", password: str = "", database: str = "market_data"):
        url = os.getenv("CLICKHOUSE_URL")
        # Basit URL parsing fallback
        if url:
            try:
                # Örn: http://default:@localhost:8123/market_data
                parts = url.split("://")[1].split("/")
                auth_host = parts[0].split("@")
                if len(auth_host) > 1:
                    creds = auth_host[0].split(":")
                    username = creds[0]
                    password = creds[1] if len(creds) > 1 else ""
                    host_port = auth_host[1].split(":")
                else:
                    host_port = auth_host[0].split(":")
                
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 8123
                database = parts[1] if len(parts) > 1 else "market_data"
            except Exception:
                pass # Use defaults if parse fails
                
        self.client = clickhouse_connect.get_client(
            host=host, 
            port=port, 
            username=username, 
            password=password, 
            database=database
        )

    async def get_bars(
        self, 
        market: str, 
        symbol: str, 
        timeframe: str, 
        start_ts: Optional[datetime] = None, 
        end_ts: Optional[datetime] = None, 
        limit: int = 1000
    ) -> List[MarketBar]:
        query = "SELECT * FROM market_bars WHERE market = {market:String} AND symbol = {symbol:String} AND timeframe = {timeframe:String}"
        params = {"market": market, "symbol": symbol, "timeframe": timeframe}
        
        if start_ts:
            query += " AND ts >= {start_ts:DateTime64}"
            params["start_ts"] = start_ts
        if end_ts:
            query += " AND ts <= {end_ts:DateTime64}"
            params["end_ts"] = end_ts
            
        query += " ORDER BY ts ASC LIMIT {limit:Int32}"
        params["limit"] = limit
        
        result = self.client.query(query, parameters=params)
        
        bars = []
        for row in result.result_rows:
            # Sütun sırası table tanımındaki ile aynı gelir
            bar = MarketBar(
                market=row[0],
                symbol=row[1],
                instrument_type=row[2],
                timeframe=row[3],
                ts=row[4],
                open=row[5],
                high=row[6],
                low=row[7],
                close=row[8],
                volume=row[9],
                source=row[10],
                source_timeframe=row[11],
                is_derived=bool(row[12]),
                quality_status=row[13],
                ingest_job_id=row[14],
                ingested_at=row[15]
            )
            bars.append(bar)
        return bars

    async def insert_bars(self, bars: List[MarketBar]) -> int:
        if not bars:
            return 0
            
        data = []
        for b in bars:
            data.append([
                b.market, b.symbol, b.instrument_type, b.timeframe, b.ts, 
                b.open, b.high, b.low, b.close, b.volume, 
                b.source, b.source_timeframe, int(b.is_derived), 
                b.quality_status, b.ingest_job_id, b.ingested_at or datetime.utcnow()
            ])
            
        column_names = [
            'market', 'symbol', 'instrument_type', 'timeframe', 'ts', 
            'open', 'high', 'low', 'close', 'volume', 
            'source', 'source_timeframe', 'is_derived', 
            'quality_status', 'ingest_job_id', 'ingested_at'
        ]
        
        self.client.insert('market_bars', data, column_names=column_names)
        return len(bars)

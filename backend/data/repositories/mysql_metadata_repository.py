import aiomysql
import os
from typing import List, Dict, Any, Optional

class MySQLMetadataRepository:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "veri_platform")
        self.password = os.getenv("MYSQL_PASSWORD", "secret123")
        self.database = os.getenv("MYSQL_DATABASE", "veri_platform_db")
        self.pool = None
        
    async def connect(self):
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                autocommit=True
            )
            
    async def get_active_instruments(self, market: Optional[str] = None) -> List[Dict[str, Any]]:
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                query = "SELECT * FROM instruments WHERE is_active = TRUE"
                params = []
                if market:
                    query += " AND market = %s"
                    params.append(market)
                    
                await cur.execute(query, params)
                return await cur.fetchall()
                
    async def update_inventory_status(self, symbol: str, market: str, timeframe: str, start_ts: str, end_ts: str, record_count: int, table_name: str="market_bars"):
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                INSERT INTO data_inventory 
                (symbol, market, timeframe, first_timestamp, last_timestamp, record_count, table_name, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                first_timestamp = LEAST(first_timestamp, VALUES(first_timestamp)),
                last_timestamp = GREATEST(last_timestamp, VALUES(last_timestamp)),
                record_count = VALUES(record_count),
                last_updated = NOW()
                """
                await cur.execute(query, (symbol, market, timeframe, start_ts, end_ts, record_count, table_name))

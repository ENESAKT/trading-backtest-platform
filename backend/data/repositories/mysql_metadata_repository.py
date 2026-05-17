import aiomysql
import os
from typing import List, Dict, Any, Optional

class MySQLMetadataRepository:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "appuser")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.database = os.getenv("MYSQL_DATABASE", "piyasapilot")
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
                
    async def update_inventory_status(self, symbol: str, market: str, timeframe: str, start_ts: str, end_ts: str, record_count: int, table_name: str = "market_bars"):
        """data_inventory tablosunu günceller.
        Kolon adları 003_inventory.sql migration ile hizalıdır:
        row_count, first_ts, last_ts, last_checked_at
        """
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                INSERT INTO data_inventory
                (symbol, market, timeframe, row_count, first_ts, last_ts, source, last_checked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                first_ts        = LEAST(first_ts, VALUES(first_ts)),
                last_ts         = GREATEST(last_ts, VALUES(last_ts)),
                row_count       = VALUES(row_count),
                source          = VALUES(source),
                last_checked_at = NOW()
                """
                await cur.execute(query, (symbol, market, timeframe, record_count, start_ts, end_ts, table_name))

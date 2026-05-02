#!/usr/bin/env python
import asyncio
import os
import sys
from loguru import logger

# Backend path access
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.repositories.clickhouse_repository import ClickHouseMarketRepository
from backend.data.repositories.mysql_metadata_repository import MySQLMetadataRepository

async def sync_inventory():
    logger.info("Starting Data Inventory Sync...")
    try:
        ch_repo = ClickHouseMarketRepository()
        mysql_repo = MySQLMetadataRepository()
        
        # Clickhouse'dan envanter ozetini alalım
        query = """
        SELECT market, symbol, timeframe, min(ts) as start_ts, max(ts) as end_ts, count(*) as cnt 
        FROM market_bars 
        GROUP BY market, symbol, timeframe
        """
        
        result = ch_repo.client.query(query)
        updates = 0
        
        for row in result.result_rows:
            market = row[0]
            symbol = row[1]
            timeframe = row[2]
            start_ts = row[3]
            end_ts = row[4]
            count = row[5]
            
            await mysql_repo.update_inventory_status(
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                start_ts=start_ts.strftime('%Y-%m-%d %H:%M:%S'),
                end_ts=end_ts.strftime('%Y-%m-%d %H:%M:%S'),
                record_count=count
            )
            updates += 1
            
        logger.info(f"Inventory sync completed successfully. {updates} series updated.")
    except Exception as e:
        logger.error(f"Error during inventory sync: {e}")

if __name__ == "__main__":
    asyncio.run(sync_inventory())

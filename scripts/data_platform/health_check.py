#!/usr/bin/env python
import asyncio
import os
import sys
from loguru import logger
import clickhouse_connect
import aiomysql
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

async def check_health():
    logger.info("Running Data Platform Health Check...")
    
    # 1. Clickhouse
    try:
        host = os.getenv("CLICKHOUSE_HOST", "localhost")
        port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
        username = os.getenv("CLICKHOUSE_USER", "default")
        password = os.getenv("CLICKHOUSE_PASSWORD", "")
        db = os.getenv("CLICKHOUSE_DB", "market_data")
        
        client = clickhouse_connect.get_client(
            host=host, 
            port=port, 
            username=username, 
            password=password, 
            database=db
        )
        res = client.query("SELECT 1")
        logger.info("[OK] ClickHouse connection successful.")
    except Exception as e:
        logger.error(f"[FAIL] ClickHouse connection failed: {e}")

    # 2. MySQL
    try:
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "veri_platform"),
            password=os.getenv("MYSQL_PASSWORD", "secret123"),
            db=os.getenv("MYSQL_DATABASE", "veri_platform_db")
        )
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        logger.info("[OK] MySQL connection successful.")
        pool.close()
        await pool.wait_closed()
    except Exception as e:
        logger.error(f"[FAIL] MySQL connection failed: {e}")

    # 3. Redis
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        await r.ping()
        logger.info("[OK] Redis connection successful.")
        await r.close()
    except Exception as e:
        logger.error(f"[FAIL] Redis connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_health())

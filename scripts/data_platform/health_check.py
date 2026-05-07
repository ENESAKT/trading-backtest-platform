#!/usr/bin/env python3
import asyncio
import os
import sys
from urllib.parse import urlparse
from loguru import logger
import clickhouse_connect
import aiomysql
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

async def check_health():
    logger.info("Running Data Platform Health Check...")
    failures = 0
    
    # 1. Clickhouse
    try:
        parsed = urlparse(os.getenv("CLICKHOUSE_URL", "http://localhost:8123/market_data"))
        host = os.getenv("CLICKHOUSE_HOST") or parsed.hostname or "localhost"
        port = int(os.getenv("CLICKHOUSE_PORT") or parsed.port or "8123")
        username = os.getenv("CLICKHOUSE_USER", "default")
        password = os.getenv("CLICKHOUSE_PASSWORD", "")
        db = os.getenv("CLICKHOUSE_DB") or (parsed.path or "/market_data").strip("/") or "market_data"
        
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
        failures += 1

    # 2. MySQL
    try:
        parsed = urlparse(os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL", "mysql://localhost:3306/metadata"))
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST") or parsed.hostname or "localhost",
            port=int(os.getenv("MYSQL_PORT") or parsed.port or 3306),
            user=os.getenv("MYSQL_USER", "veri_platform"),
            password=os.getenv("MYSQL_PASSWORD", "secret123"),
            db=os.getenv("MYSQL_DATABASE") or os.getenv("MYSQL_DB", "veri_platform_db")
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
        failures += 1

    # 3. Redis
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        await r.ping()
        logger.info("[OK] Redis connection successful.")
        await r.close()
    except Exception as e:
        logger.error(f"[FAIL] Redis connection failed: {e}")
        failures += 1

    if failures:
        return 1
    logger.info("[OK] Data platform health check passed.")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(check_health()))

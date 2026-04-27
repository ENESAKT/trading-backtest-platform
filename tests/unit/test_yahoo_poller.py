"""``YahooPoller`` ve ``BistStockPoller`` davranış testleri.

Mock'lu ``data_service`` ile gerçek yfinance çağrısı yapılmadan poller'ın
cache'e doğru yazıp yazmadığını ve hata durumunda graceful davranışı
doğrularız.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from backend.data.cache import OHLCVCache
from backend.workers.bist_poller import BistStockPoller
from backend.workers.yahoo_poller import YahooPoller


class _FakeDataService:
    def __init__(self, payload_factory):
        self.calls: list[tuple[str, str, int]] = []
        self.payload_factory = payload_factory

    def fetch_candles(self, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        self.calls.append((symbol, interval, limit))
        return self.payload_factory(symbol, interval, limit)


def _ok_payload(symbol: str, interval: str, limit: int) -> dict[str, Any]:
    bars = [
        {
            "time": 1_700_000_000 + i * 60,
            "open": 100.0 + i * 0.1,
            "high": 100.0 + i * 0.1,
            "low": 100.0 + i * 0.1,
            "close": 100.0 + i * 0.1,
            "volume": 1_000.0,
        }
        for i in range(30)
    ]
    return {
        "symbol": symbol,
        "interval": interval,
        "status": "ok",
        "bars": bars,
        "metadata": {},
    }


def _error_payload(symbol: str, interval: str, limit: int) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "status": "error",
        "bars": [],
        "metadata": {"error": "network"},
    }


@pytest.mark.asyncio
async def test_yahoo_poller_writes_each_symbol_once_per_tick(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    fake = _FakeDataService(_ok_payload)
    poller = YahooPoller(
        cache=cache,
        data_service=fake,
        symbols=["XU100", "USDTRY=X"],
        interval="15m",
        poll_seconds=10.0,  # büyük; tek tick test edeceğiz
        limit=30,
    )

    await poller.run_once()

    assert len(fake.calls) == 2
    assert {c[0] for c in fake.calls} == {"XU100", "USDTRY=X"}
    # Her sembol için 30 bar yazılmalı
    assert cache.stats().rows == 60
    assert cache.stats().distinct_symbols == 2


@pytest.mark.asyncio
async def test_yahoo_poller_skips_on_provider_error(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    fake = _FakeDataService(_error_payload)
    poller = YahooPoller(
        cache=cache,
        data_service=fake,
        symbols=["XU100"],
        interval="15m",
        poll_seconds=10.0,
    )

    await poller.run_once()

    assert fake.calls == [("XU100", "15m", YahooPoller.DEFAULT_LIMIT)]
    assert cache.stats().rows == 0  # hata → yazma yok


@pytest.mark.asyncio
async def test_yahoo_poller_loop_stops_cleanly(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    fake = _FakeDataService(_ok_payload)
    poller = YahooPoller(
        cache=cache,
        data_service=fake,
        symbols=["XU100"],
        interval="15m",
        poll_seconds=0.01,
        limit=30,
    )

    await poller.start()
    await asyncio.sleep(0.05)
    await poller.stop(timeout=1.0)

    assert poller.health().iterations >= 1
    assert not poller.running


@pytest.mark.asyncio
async def test_bist_poller_uses_60s_default_and_separate_name(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    fake = _FakeDataService(_ok_payload)
    poller = BistStockPoller(
        cache=cache,
        data_service=fake,
        symbols=["THYAO.IS"],
        interval="15m",
    )
    assert poller.name == "bist_poller"
    assert poller.interval_seconds == 60.0

    await poller.run_once()
    assert cache.stats().rows == 30

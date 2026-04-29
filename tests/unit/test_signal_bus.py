"""``backend.api.signal_bus.SignalBus`` için unit testler."""

from __future__ import annotations

import asyncio

import pytest

from backend.api.signal_bus import SignalBus


@pytest.mark.asyncio
async def test_subscribe_returns_unique_id():
    bus = SignalBus()
    cid1, q1 = await bus.subscribe()
    cid2, q2 = await bus.subscribe()
    assert cid1 != cid2 and q1 is not q2
    assert bus.stats()["subscribers"] == 2


@pytest.mark.asyncio
async def test_publish_to_all_unfiltered():
    bus = SignalBus()
    _, q1 = await bus.subscribe()
    _, q2 = await bus.subscribe()
    await bus.publish("BTCUSDT", "BUY", 100.0, "sma_crossover", "test")
    a = await asyncio.wait_for(q1.get(), timeout=0.5)
    b = await asyncio.wait_for(q2.get(), timeout=0.5)
    for msg in (a, b):
        assert msg["type"] == "signal"
        assert msg["symbol"] == "BTCUSDT"
        assert msg["signal_type"] == "BUY"
        assert msg["strategy_id"] == "sma_crossover"


@pytest.mark.asyncio
async def test_symbol_filter():
    bus = SignalBus()
    _, q = await bus.subscribe(symbols=["BTCUSDT"])
    await bus.publish("ETHUSDT", "BUY", 1, "x")
    await bus.publish("BTCUSDT", "BUY", 2, "x")
    msg = await asyncio.wait_for(q.get(), timeout=0.5)
    assert msg["symbol"] == "BTCUSDT"
    assert q.empty()


@pytest.mark.asyncio
async def test_type_filter():
    bus = SignalBus()
    _, q = await bus.subscribe(types=["SELL"])
    await bus.publish("BTCUSDT", "BUY", 1, "x")
    await bus.publish("BTCUSDT", "SELL", 2, "x")
    msg = await asyncio.wait_for(q.get(), timeout=0.5)
    assert msg["signal_type"] == "SELL"
    assert q.empty()


@pytest.mark.asyncio
async def test_unsubscribe_removes_client():
    bus = SignalBus()
    cid, _ = await bus.subscribe()
    assert bus.stats()["subscribers"] == 1
    await bus.unsubscribe(cid)
    assert bus.stats()["subscribers"] == 0


@pytest.mark.asyncio
async def test_full_queue_drops_oldest():
    bus = SignalBus(queue_max=2)
    _, q = await bus.subscribe()
    for i in range(5):
        await bus.publish("BTCUSDT", "BUY", float(i), "x")
    a = await asyncio.wait_for(q.get(), timeout=0.5)
    b = await asyncio.wait_for(q.get(), timeout=0.5)
    assert a["price"] == 3.0
    assert b["price"] == 4.0
    assert bus.stats()["dropped_total"] >= 3


@pytest.mark.asyncio
async def test_published_count_increments():
    bus = SignalBus()
    await bus.subscribe()
    await bus.publish("BTCUSDT", "BUY", 1, "x")
    await bus.publish("BTCUSDT", "SELL", 1, "x")
    assert bus.stats()["published"] == 2

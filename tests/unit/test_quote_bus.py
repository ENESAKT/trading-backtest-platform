"""``backend.api.quote_bus.QuoteBus`` için unit testler."""

from __future__ import annotations

import asyncio

import pytest

from backend.api.quote_bus import QuoteBus


def _bar(t: int, c: float = 100.0) -> dict:
    return {"time": t, "open": c, "high": c, "low": c, "close": c, "volume": 1.0}


@pytest.mark.asyncio
async def test_subscribe_returns_unique_client_id_and_queue():
    bus = QuoteBus()
    cid1, q1 = await bus.subscribe()
    cid2, q2 = await bus.subscribe()
    assert cid1 != cid2
    assert q1 is not q2
    assert bus.stats()["subscribers"] == 2


@pytest.mark.asyncio
async def test_publish_delivers_to_all_unfiltered_subscribers():
    bus = QuoteBus()
    _, q1 = await bus.subscribe()
    _, q2 = await bus.subscribe()

    await bus.publish("BTCUSDT", "15m", [_bar(t=1)])

    msg1 = await asyncio.wait_for(q1.get(), timeout=0.5)
    msg2 = await asyncio.wait_for(q2.get(), timeout=0.5)
    for msg in (msg1, msg2):
        assert msg["type"] == "bars"
        assert msg["symbol"] == "BTCUSDT"
        assert msg["interval"] == "15m"
        assert len(msg["bars"]) == 1


@pytest.mark.asyncio
async def test_symbol_filter_blocks_unrelated_messages():
    bus = QuoteBus()
    _, q = await bus.subscribe(symbols=["BTCUSDT"])

    await bus.publish("ETHUSDT", "15m", [_bar(t=1)])
    await bus.publish("BTCUSDT", "15m", [_bar(t=2)])

    msg = await asyncio.wait_for(q.get(), timeout=0.5)
    assert msg["symbol"] == "BTCUSDT"
    assert q.empty()  # ETH mesajı düşmüş olmalı


@pytest.mark.asyncio
async def test_interval_filter_works():
    bus = QuoteBus()
    _, q = await bus.subscribe(intervals=["1h"])

    await bus.publish("BTCUSDT", "15m", [_bar(t=1)])
    await bus.publish("BTCUSDT", "1h", [_bar(t=2)])

    msg = await asyncio.wait_for(q.get(), timeout=0.5)
    assert msg["interval"] == "1h"
    assert q.empty()


@pytest.mark.asyncio
async def test_publish_with_empty_bars_is_noop():
    bus = QuoteBus()
    _, q = await bus.subscribe()
    await bus.publish("BTCUSDT", "15m", [])
    assert q.empty()
    assert bus.stats()["published"] == 0


@pytest.mark.asyncio
async def test_unsubscribe_removes_client():
    bus = QuoteBus()
    cid, _ = await bus.subscribe()
    assert bus.stats()["subscribers"] == 1
    await bus.unsubscribe(cid)
    assert bus.stats()["subscribers"] == 0


@pytest.mark.asyncio
async def test_full_queue_drops_oldest():
    bus = QuoteBus(queue_max=2)
    _, q = await bus.subscribe()

    for i in range(5):
        await bus.publish("BTCUSDT", "15m", [_bar(t=i)])

    # Kuyruk 2 elemanlı; son 2 push hayatta kalmalı (drop-oldest)
    msg_a = await asyncio.wait_for(q.get(), timeout=0.5)
    msg_b = await asyncio.wait_for(q.get(), timeout=0.5)
    assert msg_a["bars"][0]["time"] == 3
    assert msg_b["bars"][0]["time"] == 4
    assert q.empty()
    assert bus.stats()["dropped_total"] >= 3

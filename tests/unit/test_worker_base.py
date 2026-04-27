"""``backend.workers.base`` için unit testler.

Worker iskeletinin lifecycle, hata yutma ve sağlık raporu davranışlarını
asyncio test'leri ile doğrular.
"""

from __future__ import annotations

import asyncio

import pytest

from backend.workers.base import AsyncWorker, WorkerSupervisor


class _CountingWorker(AsyncWorker):
    """Her tick'te sayacı artıran basit worker."""

    def __init__(self, name: str = "counter", interval: float = 0.01):
        super().__init__(name=name, interval_seconds=interval)
        self.count = 0

    async def run_once(self) -> None:
        self.count += 1


class _FlakyWorker(AsyncWorker):
    """İlk N çağrıda fırlat, sonra normal çalış."""

    def __init__(self, fail_count: int = 2):
        super().__init__(name="flaky", interval_seconds=0.01)
        self.fail_count = fail_count
        self.successes = 0

    async def run_once(self) -> None:
        if self._iterations + self._failures < self.fail_count:
            raise RuntimeError("kasti hata")
        self.successes += 1


@pytest.mark.asyncio
async def test_start_runs_loop_and_stop_halts_it():
    w = _CountingWorker(interval=0.005)
    await w.start()
    await asyncio.sleep(0.05)
    await w.stop(timeout=1.0)

    assert w.count >= 2
    assert not w.running
    h = w.health()
    assert h.iterations == w.count
    assert h.failures == 0


@pytest.mark.asyncio
async def test_failures_do_not_kill_loop():
    w = _FlakyWorker(fail_count=2)
    await w.start()
    await asyncio.sleep(0.08)
    await w.stop(timeout=1.0)

    h = w.health()
    assert h.failures >= 2
    assert h.iterations >= 1
    assert h.last_error is not None
    assert "kasti hata" in h.last_error


@pytest.mark.asyncio
async def test_double_start_is_idempotent():
    w = _CountingWorker(interval=0.01)
    await w.start()
    task_id = id(w._task)
    await w.start()  # ikinci start yeni task açmamalı
    assert id(w._task) == task_id
    await w.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_supervisor_starts_and_stops_all():
    a = _CountingWorker(name="a", interval=0.005)
    b = _CountingWorker(name="b", interval=0.005)
    sup = WorkerSupervisor([a, b])

    await sup.start_all()
    await asyncio.sleep(0.04)
    await sup.stop_all(timeout=1.0)

    assert a.count >= 1
    assert b.count >= 1
    assert not a.running
    assert not b.running

    health = sup.health()
    names = {h["name"] for h in health}
    assert names == {"a", "b"}


@pytest.mark.asyncio
async def test_stop_without_start_is_noop():
    w = _CountingWorker()
    await w.stop(timeout=0.1)  # patlamamalı
    assert not w.running

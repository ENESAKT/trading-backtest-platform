"""FastAPI lifespan + supervisor entegrasyon testi.

``TestClient`` context manager'a girince lifespan tetiklenir; çıkışta worker
durur. Test ``WorkerSupervisor``'ı sahte (lightweight) bir worker ile yükler
ve start/stop sayaçlarını doğrular.
"""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.data.cache import OHLCVCache
from backend.workers.base import AsyncWorker, WorkerSupervisor


class _PingWorker(AsyncWorker):
    def __init__(self):
        super().__init__(name="ping", interval_seconds=0.01)
        self.run_count = 0

    async def run_once(self) -> None:
        self.run_count += 1
        await asyncio.sleep(0)  # cooperative yield


class _FakeDataService:
    def fetch_default_dashboard(self):
        return {"symbols": [], "metadata": {}}

    def fetch_chart(self, symbol: str, limit: int = 180):
        return {"symbol": symbol, "status": "ok", "bars": [], "quote": None, "metadata": {}}

    def fetch_candles(self, symbol: str, interval: str = "15m", limit: int = 500):
        return {"status": "ok", "bars": [], "metadata": {}, "symbol": symbol}


def test_lifespan_starts_and_stops_workers(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    worker = _PingWorker()
    sup = WorkerSupervisor([worker])

    app = create_app(
        cache=cache,
        data_service=_FakeDataService(),
        supervisor=sup,
    )

    with TestClient(app) as client:
        # Lifespan startup → worker başlamalı
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert any(w["name"] == "ping" for w in body["workers"])
        # Worker birkaç tick atana kadar bekle
        for _ in range(50):
            if worker.run_count >= 1:
                break
            import time

            time.sleep(0.01)
        assert worker.run_count >= 1
        assert worker.running

    # Context çıkışı → lifespan shutdown → worker durmalı
    assert not worker.running


def test_health_includes_empty_workers_list_when_supervisor_empty(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    app = create_app(
        cache=cache,
        data_service=_FakeDataService(),
        supervisor=WorkerSupervisor([]),
    )
    with TestClient(app) as client:
        body = client.get("/api/health").json()
        assert body["workers"] == []

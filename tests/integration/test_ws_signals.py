"""``/ws/signals`` integration testleri.

``QuoteBus`` testlerine paralel: TestClient ``websocket_connect`` ile
publish edilen mesajların client'a düştüğünü doğrularız.
"""

from __future__ import annotations

import asyncio
import threading

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.api.quote_bus import QuoteBus
from backend.signals.signal_bus import SignalBus
from backend.data.cache import OHLCVCache
from backend.workers.base import WorkerSupervisor


class _Noop:
    def fetch_default_dashboard(self):
        return {"symbols": [], "metadata": {}}

    def fetch_chart(self, symbol, limit=180):
        return {
            "symbol": symbol,
            "status": "ok",
            "bars": [],
            "quote": None,
            "metadata": {},
        }

    def fetch_candles(self, symbol, interval="15m", limit=500):
        return {"status": "ok", "bars": [], "metadata": {}, "symbol": symbol}


def _build_client(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    bus = SignalBus()
    app = create_app(
        cache=cache,
        data_service=_Noop(),
        supervisor=WorkerSupervisor([]),
        quote_bus=QuoteBus(),
        signal_bus=bus,
    )
    return TestClient(app), bus


def _publish_in_loop(bus: SignalBus, **kwargs) -> None:
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(bus.publish(**kwargs))
    finally:
        loop.close()


def test_ws_signals_delivers_published_signal(tmp_path):
    client, bus = _build_client(tmp_path)
    with client.websocket_connect("/ws/signals") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"

        t = threading.Thread(
            target=_publish_in_loop,
            kwargs={"bus": bus, "symbol": "BTCUSDT", "signal_type": "BUY",
                    "price": 100.0, "strategy_id": "sma_crossover",
                    "reason": "test", "interval": "15m"},
        )
        t.start()
        t.join(timeout=2.0)

        msg = ws.receive_json()
        assert msg["type"] == "signal"
        assert msg["symbol"] == "BTCUSDT"
        assert msg["signal_type"] == "BUY"
        assert msg["strategy_id"] == "sma_crossover"


def test_ws_signals_filters_by_symbol(tmp_path):
    client, bus = _build_client(tmp_path)
    with client.websocket_connect("/ws/signals?symbols=BTCUSDT") as ws:
        ws.receive_json()  # ready
        ignored = threading.Thread(
            target=_publish_in_loop,
            kwargs={
                "bus": bus,
                "symbol": "ETHUSDT",
                "signal_type": "BUY",
                "price": 1.0,
                "strategy_id": "x",
            },
        )
        matched = threading.Thread(
            target=_publish_in_loop,
            kwargs={
                "bus": bus,
                "symbol": "BTCUSDT",
                "signal_type": "BUY",
                "price": 1.0,
                "strategy_id": "x",
            },
        )
        ignored.start()
        ignored.join(timeout=2.0)
        matched.start()
        matched.join(timeout=2.0)
        msg = ws.receive_json()
        assert msg["symbol"] == "BTCUSDT"


def test_health_includes_signal_bus_stats(tmp_path):
    client, _ = _build_client(tmp_path)
    body = client.get("/api/health").json()
    assert "signal_bus" in body
    assert "signal_generator" in body
    assert body["signal_bus"]["subscribers"] == 0

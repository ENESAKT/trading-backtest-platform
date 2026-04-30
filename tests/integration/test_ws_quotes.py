"""``/ws/quotes`` endpoint integration testleri.

FastAPI ``TestClient.websocket_connect`` ile sahte bus'a publish edilen
mesajların client'a düştüğünü doğrularız.
"""

from __future__ import annotations

import asyncio
import threading

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.api.quote_bus import QuoteBus
from backend.data.cache import OHLCVCache
from backend.workers.base import WorkerSupervisor


class _FakeDataService:
    def fetch_default_dashboard(self):
        return {"symbols": [], "metadata": {}}

    def fetch_chart(self, symbol, limit=180):
        return {"symbol": symbol, "status": "ok", "bars": [], "quote": None, "metadata": {}}

    def fetch_candles(self, symbol, interval="15m", limit=500):
        return {"status": "ok", "bars": [], "metadata": {}, "symbol": symbol}


def _build_client(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    bus = QuoteBus()
    app = create_app(
        cache=cache,
        data_service=_FakeDataService(),
        supervisor=WorkerSupervisor([]),
        quote_bus=bus,
    )
    return TestClient(app), bus


def _publish_in_loop(bus: QuoteBus, symbol: str, interval: str, bar: dict) -> None:
    """``TestClient`` event loop'unda publish çağır (sync test bağlamından)."""
    # FastAPI TestClient her request için yeni bir event loop kullanır; bus
    # state'i process-global. Threadsafe olmayan ``asyncio.Lock`` kullandığımız
    # için publish'i bus'ın olay döngüsünde çağırmak şart.
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(bus.publish(symbol, interval, [bar]))
    finally:
        loop.close()


def test_ws_quotes_delivers_published_bar(tmp_path):
    client, bus = _build_client(tmp_path)
    bar = {"time": 1, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}

    with client.websocket_connect("/ws/quotes") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert "client_id" in ready

        # Publish'i ws'in event loop'unda çalıştırmak için arka thread + yeni loop
        # — TestClient context'i içinde portal kuyruk dolar.
        t = threading.Thread(
            target=_publish_in_loop, args=(bus, "BTCUSDT", "15m", bar)
        )
        t.start()
        t.join(timeout=2.0)

        msg = ws.receive_json()
        assert msg["type"] == "bars"
        assert msg["symbol"] == "BTCUSDT"
        assert msg["interval"] == "15m"
        assert msg["bars"][0]["close"] == 1.0


def test_ws_quotes_symbol_filter_via_query(tmp_path):
    client, bus = _build_client(tmp_path)
    bar = {"time": 1, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}

    with client.websocket_connect("/ws/quotes?symbols=BTCUSDT") as ws:
        ws.receive_json()  # ready

        # ETH yayını filtreyle düşmeli
        threading.Thread(
            target=_publish_in_loop, args=(bus, "ETHUSDT", "15m", bar)
        ).start()
        # BTC yayını gelmeli
        threading.Thread(
            target=_publish_in_loop, args=(bus, "BTCUSDT", "15m", bar)
        ).start()

        msg = ws.receive_json()
        assert msg["symbol"] == "BTCUSDT"


def test_ws_disconnect_cleans_up_subscriber(tmp_path):
    client, bus = _build_client(tmp_path)

    with client.websocket_connect("/ws/quotes") as ws:
        ws.receive_json()
        # subscribers en az 1 olmalı (handler subscribe etmiş)
        # Anlık doğrulama: publish kuyruk dolduğunu gör
        bar = {"time": 1, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}
        threading.Thread(
            target=_publish_in_loop, args=(bus, "BTCUSDT", "15m", bar)
        ).start()
        ws.receive_json()

    # Context çıkışı → unsubscribe çağrılmalı
    # subscribers sayısının 0'a düşmesi için handler'ın finally bloğu
    # tamamlanmalı; bu birkaç event-loop tick alır.
    import time

    for _ in range(50):
        if bus.stats()["subscribers"] == 0:
            break
        time.sleep(0.02)
    assert bus.stats()["subscribers"] == 0


def test_health_includes_quote_bus_stats(tmp_path):
    client, _ = _build_client(tmp_path)
    body = client.get("/api/health").json()
    assert "quote_bus" in body
    assert body["quote_bus"]["subscribers"] == 0
    assert body["quote_bus"]["published"] == 0

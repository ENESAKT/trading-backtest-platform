"""FastAPI gateway integration testleri.

``backend.api.main.create_app`` factory'si ile mock'lu LiveDataService
enjeksiyonu yapıyoruz; gerçek yfinance/Binance çağrısı yok.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.data.cache import OHLCVCache


class FakeLiveDataService:
    """Gerçek provider'a hiç gitmeyen, kontrollü payload üreten mock."""

    def __init__(self):
        self.calls = 0
        self.next_payload: dict[str, Any] | None = None

    def fetch_default_dashboard(self) -> dict[str, Any]:
        return {"symbols": [], "metadata": {"read_only": True}}

    def fetch_chart(self, symbol: str, limit: int = 180) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "status": "ok",
            "bars": [],
            "quote": {"last": 100.0, "timestamp": "2026-04-27T10:00:00+00:00"},
            "metadata": {"source": "mock", "fetched_at": "2026-04-27T10:00:00+00:00"},
        }

    def fetch_candles(
        self, symbol: str, interval: str = "15m", limit: int = 500
    ) -> dict[str, Any]:
        self.calls += 1
        if self.next_payload is not None:
            return self.next_payload
        if not symbol:
            return {
                "status": "error",
                "message": "Sembol zorunludur.",
                "bars": [],
                "quote": None,
                "metadata": {"error": "symbol_required", "read_only": True},
            }
        if interval not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}:
            return {
                "status": "error",
                "message": f"Geçersiz interval: {interval}",
                "bars": [],
                "quote": None,
                "metadata": {"error": "invalid_interval", "read_only": True},
            }
        # 30 bar üret (spike filter trip etmesin diye düzgün artış)
        bars = [
            {
                "time": 1700000000 + i * 60,
                "open": 100.0 + i * 0.1,
                "high": 100.0 + i * 0.1,
                "low": 100.0 + i * 0.1,
                "close": 100.0 + i * 0.1,
                "volume": 1000.0,
            }
            for i in range(30)
        ]
        return {
            "symbol": symbol.upper(),
            "display_name": symbol,
            "market": "crypto",
            "interval": interval,
            "status": "ok",
            "message": "",
            "bars": bars,
            "quote": {"last": bars[-1]["close"], "timestamp": "2026-04-27T10:00:00+00:00"},
            "metadata": {"source": "mock-binance", "read_only": True},
        }


def _build_client(tmp_path) -> tuple[TestClient, FakeLiveDataService, OHLCVCache]:
    cache = OHLCVCache(db_path=tmp_path / "ohlcv.sqlite3")
    fake = FakeLiveDataService()
    app = create_app(cache=cache, data_service=fake)
    return TestClient(app), fake, cache


def test_health_returns_cache_stats(tmp_path):
    client, _, _ = _build_client(tmp_path)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["read_only"] is True
    assert body["cache"]["rows"] == 0
    assert "fetched_at" in body


def test_v2_candles_writes_to_cache_on_first_call(tmp_path):
    client, fake, cache = _build_client(tmp_path)
    resp = client.get("/api/v2/candles", params={
        "symbol": "BTCUSDT", "interval": "15m", "limit": 30,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert len(body["bars"]) == 30
    assert body["metadata"]["cache"] == "miss_then_write"
    assert "spike_filter" in body["metadata"]
    # Cache'e yazılmış olmalı
    assert cache.stats().rows == 30
    assert fake.calls == 1


def test_v2_candles_rejects_empty_symbol(tmp_path):
    client, _, _ = _build_client(tmp_path)
    resp = client.get("/api/v2/candles", params={"symbol": "", "interval": "15m"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert body["metadata"]["error"] == "symbol_required"


def test_v2_candles_rejects_invalid_interval(tmp_path):
    client, _, _ = _build_client(tmp_path)
    resp = client.get("/api/v2/candles", params={
        "symbol": "BTCUSDT", "interval": "bogus",
    })
    assert resp.status_code == 400
    body = resp.json()
    assert body["metadata"]["error"] == "invalid_interval"


def test_v2_candles_falls_back_to_cache_on_provider_error(tmp_path):
    client, fake, cache = _build_client(tmp_path)
    # 1) Önce sağlıklı çağrı → cache dolar
    client.get("/api/v2/candles", params={
        "symbol": "BTCUSDT", "interval": "15m", "limit": 30,
    })
    assert cache.stats().rows == 30

    # 2) Provider hata döndürsün
    fake.next_payload = {
        "status": "error",
        "message": "Bağlantı Hatası",
        "bars": [],
        "quote": None,
        "metadata": {"error": "network", "read_only": True},
    }
    resp = client.get("/api/v2/candles", params={
        "symbol": "BTCUSDT", "interval": "15m", "limit": 30,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stale"
    assert len(body["bars"]) == 30
    assert body["metadata"]["cache"] == "fallback"
    assert "provider_error" in body["metadata"]


def test_legacy_v1_endpoints_still_respond(tmp_path):
    client, _, _ = _build_client(tmp_path)
    # /api/market/defaults
    r1 = client.get("/api/market/defaults")
    assert r1.status_code == 200
    # /api/market/chart
    r2 = client.get("/api/market/chart", params={"symbol": "BTCUSDT", "limit": 50})
    assert r2.status_code == 200
    # /api/market/chart boş symbol → 400
    r3 = client.get("/api/market/chart", params={"symbol": ""})
    assert r3.status_code == 400

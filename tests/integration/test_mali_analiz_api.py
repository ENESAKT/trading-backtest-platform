"""Mali analiz API v2 entegrasyon testleri — borsapy tabanlı yeni endpoint'ler."""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.workers import WorkerSupervisor

# Test ortamında gerçek MySQL bağlantısı ve borsapy harvest yok.
_TEST_ENV = {
    "PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY": "1",
    "PIYASAPILOT_DISABLE_FINANCIAL_HARVEST": "1",
    "PIYASAPILOT_DISABLE_DB_FACADE": "1",
    "PIYASAPILOT_DISABLE_WORKERS": "1",
}


def _client() -> TestClient:
    """DB olmadan minimal app — tüm mali-analiz endpoint'leri 'no_db' / boş döner."""
    orig = {k: os.environ.get(k) for k in _TEST_ENV}
    os.environ.update(_TEST_ENV)
    try:
        app = create_app(supervisor=WorkerSupervisor([]))
    finally:
        for k, v in orig.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return TestClient(app)


# ── Universe ──────────────────────────────────────────────────────────────────

def test_universe_returns_bist30_list():
    client = _client()
    resp = client.get("/api/mali-analiz/universe")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scope"] == "bist30"
    assert body["source"] == "borsapy"
    symbols = [s["symbol"] for s in body["symbols"]]
    assert "THYAO" in symbols
    assert "AKBNK" in symbols
    assert len(symbols) == 30


def test_universe_symbol_has_required_fields():
    client = _client()
    body = client.get("/api/mali-analiz/universe").json()
    thyao = next(s for s in body["symbols"] if s["symbol"] == "THYAO")
    assert thyao["ticker"] == "THYAO.IS"
    assert thyao["name"]  # Türk Hava Yolları
    assert "fetch_status" in thyao


# ── Alerts ────────────────────────────────────────────────────────────────────

def test_alerts_returns_empty_without_db():
    client = _client()
    resp = client.get("/api/mali-analiz/alerts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["alerts"] == []
    assert body["source"] == "no_db"


def test_alerts_mark_read_graceful_without_db():
    client = _client()
    resp = client.post("/api/mali-analiz/alerts/mark-read", json={"ids": [1, 2]})
    assert resp.status_code == 200
    assert resp.json()["marked"] == 2


# ── Symbol validation ─────────────────────────────────────────────────────────

def test_invalid_symbol_returns_400():
    client = _client()
    for endpoint in ["balance-sheet", "income-stmt", "cashflow", "ratios", "summary"]:
        resp = client.get(f"/api/mali-analiz/%20/{endpoint}")  # URL-encoded space
        assert resp.status_code == 400, f"{endpoint} should reject empty symbol"
        assert "symbol boş olamaz" in resp.json()["detail"]


def test_bist_suffix_normalized():
    """THYAO.IS → THYAO normalizasyonu."""
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO.IS/reports")
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "THYAO"


# ── Balance sheet / income / cashflow (no DB) ─────────────────────────────────

@pytest.mark.parametrize("endpoint,key", [
    ("balance-sheet", "rows"),
    ("income-stmt",   "rows"),
    ("cashflow",      "rows"),
])
def test_statement_endpoints_return_empty_without_db(endpoint, key):
    client = _client()
    resp = client.get(f"/api/mali-analiz/THYAO/{endpoint}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert body[key] == []
    assert body["periods"] == []
    assert body["source"] == "no_db"


# ── Ratios ────────────────────────────────────────────────────────────────────

def test_ratios_returns_empty_without_db():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/ratios")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert body["ratios"] == []
    assert body["source"] == "no_db"


# ── Summary ───────────────────────────────────────────────────────────────────

def test_summary_returns_empty_without_db():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert body["alerts"] == []
    assert body["source"] == "no_db"


# ── Reports / events / metric-history (eski uyumluluk) ───────────────────────

def test_reports_returns_periods_list():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/reports")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert "periods" in body
    assert isinstance(body["periods"], list)


def test_events_returns_events_list():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert "events" in body
    assert isinstance(body["events"], list)


def test_metric_history_returns_points():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/metric-history", params={"metric": "roe"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert body["metric"] == "roe"
    assert "points" in body
    assert isinstance(body["points"], list)


# ── Chart data ────────────────────────────────────────────────────────────────

def test_chart_data_returns_metrics_dict():
    client = _client()
    resp = client.get("/api/mali-analiz/THYAO/chart-data")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "THYAO"
    assert "metrics" in body
    assert isinstance(body["metrics"], dict)


# ── Refresh endpoints return 503 without DB ───────────────────────────────────

def test_refresh_single_symbol_503_without_db():
    client = _client()
    resp = client.post("/api/mali-analiz/THYAO/refresh")
    assert resp.status_code == 503


def test_refresh_all_503_without_db():
    client = _client()
    resp = client.post("/api/mali-analiz/refresh")
    assert resp.status_code == 503

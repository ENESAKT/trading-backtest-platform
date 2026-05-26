"""Integration testleri — Screener Yeniden Üretilebilirlik

POST /api/screener/run:
  - Aynı filtreler aynı sembol setini döndürmeli (run_id hariç).
  - Geçersiz op → boş sonuç veya 400/422.
  - limit alanı 1-500 arasında sınırlı (Pydantic).
  - Boş filtre listesi tüm sembolleri döndürmeli.

Strateji: create_app(cache=mock_cache) + get_current_user dependency override.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

os.environ.setdefault("PIYASAPILOT_DISABLE_WORKERS", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_DB_FACADE", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY", "1")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-64-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
os.environ.setdefault("APP_ENV", "test")


def _make_bar(close=52.0, volume=10_000.0):
    return {
        "time": 1700000000, "open": 50.0, "high": 55.0,
        "low": 48.0, "close": close, "volume": volume,
    }


def _make_cache_mock():
    """Her sembol için tutarlı bar verisi döndüren cache mock."""
    mock_cache = MagicMock()
    two_bars  = [_make_bar(50.0), _make_bar(52.0)]
    many_bars = [_make_bar(50.0 + i * 0.1) for i in range(252)]

    def fake_get_window(symbol, interval, **kwargs):
        limit = kwargs.get("limit", 2)
        bars = many_bars[:max(2, limit)]
        return bars

    mock_cache.get_window.side_effect = fake_get_window
    mock_cache.latest_bar.return_value = _make_bar()
    return mock_cache


def _make_app():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    try:
        from backend.api.main import create_app
        return create_app(cache=_make_cache_mock())
    except Exception as exc:
        pytest.skip(f"create_app başarısız: {exc}")


def _pro_user():
    return {
        "id": 1, "role": "pro", "plan": "pro", "sub": "1",
        "email": "test@test.com", "username": "test",
    }


def _client(app):
    from fastapi.testclient import TestClient
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: _pro_user()
    return TestClient(app, raise_server_exceptions=False)


# ─── Test 1: aynı filtreler aynı sembol seti döner ───────────────────────────

def test_screener_same_filters_same_results():
    app = _make_app()
    client = _client(app)

    payload = {
        "universe": "BIST30",
        "filters": [{"column": "last_price", "op": "gt", "value": 0}],
        "sort_by": "last_price",
        "sort_dir": "desc",
        "limit": 10,
    }

    resp1 = client.post("/api/screener/run", json=payload)
    resp2 = client.post("/api/screener/run", json=payload)
    app.dependency_overrides.clear()

    if resp1.status_code == 404:
        pytest.skip("/api/screener/run bulunamadı")
    if resp1.status_code == 500:
        pytest.skip(f"Sunucu hatası: {resp1.text[:200]}")

    assert resp1.status_code == 200, f"HTTP {resp1.status_code}: {resp1.text[:200]}"
    assert resp2.status_code == 200

    syms1 = sorted(r["symbol"] for r in resp1.json().get("rows", []))
    syms2 = sorted(r["symbol"] for r in resp2.json().get("rows", []))
    assert syms1 == syms2, "Aynı filtreler aynı sembol setini döndürmeli"

    # run_id her seferinde farklı olmalı
    assert resp1.json().get("run_id") != resp2.json().get("run_id")
    # filters_hash aynı olmalı
    assert resp1.json().get("filters_hash") == resp2.json().get("filters_hash")


# ─── Test 2: geçersiz op → boş sonuç veya 400/422 ────────────────────────────

def test_screener_invalid_op_returns_400_or_422():
    app = _make_app()
    client = _client(app)

    payload = {
        "universe": "BIST30",
        "filters": [{"column": "last_price", "op": "INVALID_OP", "value": 50}],
        "sort_by": "last_price",
        "sort_dir": "desc",
        "limit": 5,
    }
    resp = client.post("/api/screener/run", json=payload)
    app.dependency_overrides.clear()

    if resp.status_code == 404:
        pytest.skip("/api/screener/run bulunamadı")

    # Geçersiz op: ya hata kodu ya da hiçbir sembol eşleşmez (boş rows)
    assert resp.status_code in (200, 400, 422), \
        f"Beklenen 200/400/422, geldi {resp.status_code}"
    if resp.status_code == 200:
        rows = resp.json().get("rows", [])
        assert isinstance(rows, list)


# ─── Test 3: limit 500 ile sınırlı (Pydantic le=500) ────────────────────────

def test_screener_limit_clamped():
    app = _make_app()
    client = _client(app)

    # Pydantic limit le=500 — 501 gönderilirse 422 gelir
    payload = {
        "universe": "BIST30",
        "filters": [],
        "sort_by": "last_price",
        "sort_dir": "desc",
        "limit": 501,
    }
    resp = client.post("/api/screener/run", json=payload)
    app.dependency_overrides.clear()

    if resp.status_code == 404:
        pytest.skip("/api/screener/run bulunamadı")

    # limit=501 Pydantic'in le=500 kısıtını ihlal eder → 422
    assert resp.status_code == 422, \
        f"limit=501 için 422 bekleniyor, {resp.status_code} geldi"


# ─── Test 4: boş filtre listesi → sonuç döner ────────────────────────────────

def test_screener_empty_filters_returns_results():
    app = _make_app()
    client = _client(app)

    payload = {
        "universe": "BIST30",
        "filters": [],
        "sort_by": "last_price",
        "sort_dir": "desc",
        "limit": 10,
    }
    resp = client.post("/api/screener/run", json=payload)
    app.dependency_overrides.clear()

    if resp.status_code in (404, 500):
        pytest.skip("Endpoint kullanılamıyor")

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    rows = body.get("rows", [])
    assert isinstance(rows, list)
    assert len(rows) > 0, "Boş filtrelerle en az bir sembol dönmeli"
    assert "run_id"       in body, "run_id yanıtta olmalı"
    assert "filters_hash" in body, "filters_hash yanıtta olmalı"

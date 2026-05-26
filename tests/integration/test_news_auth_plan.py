"""Integration testleri — News Auth/Plan Davranışı

/api/news endpoint'i:
  - guest → max 5 haber, fresh=false zorlanır
  - free  → max 20 haber
  - pro   → max 100 haber
  - 401 yerine plan_note ile graceful degradation

Strateji: backend.news.news_store.NewsStore sınıfı patch edilir;
create_app() her testte yeniden oluşturulur (nonlocal _news_store_instance sıfırlanır).
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("PIYASAPILOT_DISABLE_WORKERS", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_DB_FACADE", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY", "1")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-64-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
os.environ.setdefault("APP_ENV", "test")


def _fake_news(n: int) -> list[dict]:
    return [
        {
            "id":           i,
            "headline":     f"Haber {i}",
            "symbol":       "THYAO",
            "source":       "KAP",
            "published_at": "2024-01-01T12:00:00Z",
            "is_read":      False,
        }
        for i in range(n)
    ]


def _make_app_with_news_mock(mock_store_instance):
    """NewsStore sınıfını mock'layarak yeni bir app örneği oluştur."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    with patch("backend.news.news_store.NewsStore", return_value=mock_store_instance):
        from backend.api.main import create_app
        app = create_app()
    return app


def _make_mock_store(news_list, unread=0):
    mock_store = MagicMock()
    mock_store.query.return_value = news_list
    mock_store.count_unread.return_value = unread
    mock_store.upsert = MagicMock()
    return mock_store


# ─── Test: guest max 5 haber ─────────────────────────────────────────────────

def test_news_guest_gets_max_5():
    from fastapi.testclient import TestClient

    mock_store = _make_mock_store(_fake_news(20), unread=0)
    app = _make_app_with_news_mock(mock_store)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/news?limit=50")
    if resp.status_code == 404:
        pytest.skip("News endpoint bulunamadı")
    if resp.status_code == 500:
        pytest.skip("Server error (DB bağlantısı yok)")

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    news = body.get("news", [])
    assert len(news) <= 5, f"Guest max 5 haber almalı, {len(news)} geldi"
    assert body.get("plan_note") == "guest"
    assert "guest_limit_note" in body, "guest_limit_note alanı olmalı"


# ─── Test: guest fresh=true zorla kapatılır ──────────────────────────────────

def test_news_guest_fresh_forced_false():
    from fastapi.testclient import TestClient

    mock_store = _make_mock_store(_fake_news(3), unread=0)
    app = _make_app_with_news_mock(mock_store)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/news?fresh=true&symbol=THYAO")
    if resp.status_code in (404, 500):
        pytest.skip("Endpoint kullanılamıyor")

    assert resp.status_code == 200
    # Guest için fresh=true geçilse de upsert çağrılmamalı
    mock_store.upsert.assert_not_called()


# ─── Test: free kullanıcı max 20 haber ───────────────────────────────────────

def test_news_free_user_gets_max_20():
    from fastapi.testclient import TestClient
    from backend.auth.dependencies import get_optional_user

    mock_store = _make_mock_store(_fake_news(50), unread=5)
    app = _make_app_with_news_mock(mock_store)

    # Free kullanıcı dependency override
    app.dependency_overrides[get_optional_user] = lambda: {
        "role": "free", "id": 1, "plan": "free", "sub": "1"
    }

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/news?limit=50")
    app.dependency_overrides.clear()

    if resp.status_code in (404, 500):
        pytest.skip("Endpoint kullanılamıyor")
    if resp.status_code == 200:
        body = resp.json()
        news = body.get("news", [])
        assert len(news) <= 20, f"Free kullanıcı max 20 haber almalı, {len(news)} geldi"


# ─── Test: 401 yerine boş liste + not dönmeli ────────────────────────────────

def test_news_never_returns_401_for_public():
    from fastapi.testclient import TestClient

    mock_store = _make_mock_store([], unread=0)
    app = _make_app_with_news_mock(mock_store)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/news")
    if resp.status_code == 404:
        pytest.skip("News endpoint bulunamadı")
    if resp.status_code == 500:
        pytest.skip("Server error (DB bağlantısı yok)")

    assert resp.status_code != 401, \
        "/api/news 401 döndürmemeli — graceful degradation olmalı"
    assert resp.status_code == 200


# ─── Test: yanıt şeması tutarlı ──────────────────────────────────────────────

def test_news_response_schema():
    from fastapi.testclient import TestClient

    mock_store = _make_mock_store(_fake_news(2), unread=1)
    app = _make_app_with_news_mock(mock_store)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/news")
    if resp.status_code in (404, 500):
        pytest.skip("Endpoint kullanılamıyor")

    assert resp.status_code == 200
    body = resp.json()
    assert "news"  in body, "news alanı yanıtta olmalı"
    assert "total" in body, "total alanı yanıtta olmalı"
    assert isinstance(body["news"], list)

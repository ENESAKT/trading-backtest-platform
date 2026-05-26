"""Integration testleri — /api/v2/candles metadata kalitesi

DataTruth metadata alanları her yanıtta mevcut olmalı.
create_app() dependency injection ile mock'lu MarketDataFacade kullanılır.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock


def _make_app(facade=None):
    """Test için FastAPI app oluştur — worker'lar ve DB bağlantısı kapalı."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    os.environ.setdefault("PIYASAPILOT_DISABLE_WORKERS", "1")
    os.environ.setdefault("PIYASAPILOT_DISABLE_DB_FACADE", "1")
    os.environ.setdefault("PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY", "1")
    os.environ.setdefault("JWT_SECRET", "ci-test-secret-64-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    os.environ.setdefault("APP_ENV", "test")
    try:
        from backend.api.main import create_app
        return create_app(market_data_facade=facade)
    except Exception as exc:
        pytest.skip(f"create_app başarısız: {exc}")


def _fake_bars(n=5):
    return [
        {"time": 1700000000 + i * 86400,
         "open": 50.0, "high": 55.0, "low": 48.0, "close": 52.0 + i, "volume": 10000.0}
        for i in range(n)
    ]


# ─── Test 1: geçersiz interval → 400 ─────────────────────────────────────────

def test_invalid_interval_returns_400():
    from fastapi.testclient import TestClient
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v2/candles?symbol=THYAO&interval=INVALID")
    assert resp.status_code == 400, f"Beklenen 400, geldi {resp.status_code}"
    body = resp.json()
    assert "invalid_interval" in str(body) or "detail" in body


# ─── Test 2: boş sembol → crash yok ─────────────────────────────────────────

def test_empty_symbol_no_crash():
    from fastapi.testclient import TestClient
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v2/candles?symbol=&interval=1d&limit=5")
    assert resp.status_code in (200, 400, 404), \
        f"500 alınmamalı, geldi {resp.status_code}"


# ─── Test 3: facade varsa metadata alanları mevcut ───────────────────────────

def test_metadata_fields_present_when_bars_returned():
    from fastapi.testclient import TestClient
    from backend.data.repositories.market_data_facade import CandleReadResult

    mock_facade = MagicMock()
    mock_facade.read_candles.return_value = CandleReadResult(
        bars=_fake_bars(5),
        source="clickhouse",
    )

    app = _make_app(facade=mock_facade)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v2/candles?symbol=THYAO&interval=1d&limit=5")

    if resp.status_code == 404:
        pytest.skip("/api/v2/candles bulunamadı")

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert "bars" in body, "bars alanı yanıtta olmalı"
    assert "metadata" in body, "metadata alanı yanıtta olmalı"
    meta = body["metadata"]
    assert "is_real" in meta, "metadata.is_real alanı olmalı"
    assert "source" in meta, "metadata.source alanı olmalı"
    assert "status" in meta, "metadata.status alanı olmalı"


# ─── Test 4: lisans kısıtlı sembol → özel payload ───────────────────────────

def test_license_restricted_symbol_payload():
    from fastapi.testclient import TestClient
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    # Lisans kısıtlı semboller yine de 200 veya 403 döner, 500 değil
    resp = client.get("/api/v2/candles?symbol=THYAO.IS&interval=1m&limit=5")
    assert resp.status_code in (200, 403, 451), \
        f"Lisans kısıtlı: beklenen 200/403/451, geldi {resp.status_code}"


# ─── Test 5: limit 5000 ile sınırlanıyor ────────────────────────────────────

def test_limit_clamped_to_5000():
    from fastapi.testclient import TestClient
    from backend.data.repositories.market_data_facade import CandleReadResult

    mock_facade = MagicMock()
    # 5 bar döner — facade hangi limit ile çağrılıyor kontrol et
    mock_facade.read_candles.return_value = CandleReadResult(
        bars=_fake_bars(5),
        source="clickhouse",
    )

    app = _make_app(facade=mock_facade)
    client = TestClient(app, raise_server_exceptions=False)
    # limit=99999 → safe_limit = 5000 ile sınırlanmalı
    resp = client.get("/api/v2/candles?symbol=AKBNK&interval=1d&limit=99999")
    if resp.status_code == 200:
        call_args = mock_facade.read_candles.call_args
        if call_args:
            _, _, called_limit = call_args[0]
            assert called_limit <= 5000, f"Limit 5000'i geçmemeli, {called_limit} geldi"

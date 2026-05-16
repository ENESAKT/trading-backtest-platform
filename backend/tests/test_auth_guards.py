"""
test_auth_guards.py — Korumalı endpoint'lere token'sız erişimde 401 döndürülmesini test eder.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.anyio


# Korumalı GET endpoint'leri
PROTECTED_GET_ENDPOINTS = [
    "/api/backtest/strategies",
    "/api/backtest/reports",
    "/api/backtest/reports/fake-id",
    "/api/backtest/reports/fake-id/export",
    "/api/paper/wallets",
    "/api/paper/trades",
    "/api/paper/trades/export",
    "/api/paper/equity?strategy_id=test",
    "/api/strategy-lab/strategies",
    "/api/strategy-lab/strategies/1",
    "/api/strategy-lab/paper",
    "/api/news",
    "/api/news/unread-count",
    "/api/alerts/price",
    "/api/technical/BTCUSDT",
    "/api/mali-analiz/universe",
    "/api/mali-analiz/alerts",
    "/api/mali-analiz/comparison",
    "/api/mali-analiz/THYAO/summary",
    "/api/mali-analiz/THYAO/ratios",
    "/api/mali-analiz/THYAO/balance-sheet",
    "/api/mali-analiz/THYAO/income-stmt",
    "/api/mali-analiz/THYAO/cashflow",
    "/api/mali-analiz/THYAO/reports",
    "/api/mali-analiz/THYAO/events",
    "/api/mali-analiz/THYAO/metric-history",
    "/api/mali-analiz/THYAO/chart-data",
]

# Korumalı POST endpoint'leri
PROTECTED_POST_ENDPOINTS = [
    "/api/backtest/run",
    "/api/backtest/optimize",
    "/api/backtest/scan",
    "/api/backtest/walk-forward",
    "/api/backtest/monte-carlo",
    "/api/backtest/compare",
    "/api/strategy-lab/strategies",
    "/api/strategy-lab/pack/export",
    "/api/strategy-lab/pack/import",
    "/api/strategy-lab/strategies/1/paper/activate",
    "/api/strategy-lab/paper/1/deactivate",
    "/api/paper/reset/test",
    "/api/paper/halt/test",
    "/api/paper/resume/test",
    "/api/paper/signal",
    "/api/backtest/reports/fake/paper/activate",
    "/api/news/mark-read",
    "/api/alerts/price",
    "/api/mali-analiz/alerts/mark-read",
    "/api/mali-analiz/refresh",
    "/api/mali-analiz/recompute",
    "/api/mali-analiz/THYAO/recompute",
    "/api/mali-analiz/THYAO/refresh",
]

# Korumalı DELETE endpoint'leri
PROTECTED_DELETE_ENDPOINTS = [
    "/api/backtest/reports/fake-id",
    "/api/strategy-lab/strategies/1",
    "/api/alerts/price/1",
]

# Herkese açık endpoint'ler (401 dönmemeli)
PUBLIC_ENDPOINTS = [
    "/api/health",
]


@pytest.fixture()
def app():
    from backend.api.main import create_app
    return create_app()


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
async def test_get_without_token_returns_401(client, path):
    """GET endpoint token'sız çağrıldığında 401 dönmeli."""
    resp = await client.get(path)
    assert resp.status_code == 401, f"GET {path} → {resp.status_code}, beklenen 401"


@pytest.mark.parametrize("path", PROTECTED_POST_ENDPOINTS)
async def test_post_without_token_returns_401(client, path):
    """POST endpoint token'sız çağrıldığında 401 dönmeli."""
    resp = await client.post(path, json={})
    assert resp.status_code == 401, f"POST {path} → {resp.status_code}, beklenen 401"


@pytest.mark.parametrize("path", PROTECTED_DELETE_ENDPOINTS)
async def test_delete_without_token_returns_401(client, path):
    """DELETE endpoint token'sız çağrıldığında 401 dönmeli."""
    resp = await client.delete(path)
    assert resp.status_code == 401, f"DELETE {path} → {resp.status_code}, beklenen 401"


@pytest.mark.parametrize("path", PUBLIC_ENDPOINTS)
async def test_public_endpoints_no_auth_needed(client, path):
    """Herkese açık endpoint'ler token'sız 200 dönmeli."""
    resp = await client.get(path)
    assert resp.status_code == 200, f"GET {path} → {resp.status_code}, beklenen 200"

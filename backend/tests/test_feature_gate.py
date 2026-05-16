"""
test_feature_gate.py — Feature gate ve plan limit testleri.

Free plan kısıtlamaları:
  - max 3 saved strategy
  - max 10 backtest/gün
  - paper trading kapalı (POST /api/paper/* → 403)

Pro plan:
  - sınırsız strateji & backtest
  - paper trading açık

Ultra plan:
  - hepsi + api_access
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.auth.feature_gate import can_access, get_limits, get_quota

pytestmark = pytest.mark.anyio


# ── Unit Tests ────────────────────────────────────────────────────────────────

class TestPlanLimits:
    """Feature gate unit testleri."""

    def test_free_backtest_limit(self):
        assert get_quota("free", "backtest_runs_per_day") == 10

    def test_free_max_strategies(self):
        assert get_limits("free").max_saved_strategies == 3

    def test_free_no_paper_trading(self):
        assert not can_access("free", "paper_trading")

    def test_pro_unlimited_backtest(self):
        assert get_quota("pro", "backtest_runs_per_day") == -1

    def test_pro_unlimited_strategies(self):
        assert get_limits("pro").max_saved_strategies == -1

    def test_pro_paper_trading(self):
        assert can_access("pro", "paper_trading")

    def test_ultra_api_access(self):
        assert can_access("ultra", "api_access")

    def test_free_no_api_access(self):
        assert not can_access("free", "api_access")

    def test_unknown_role_falls_back_to_free(self):
        limits = get_limits("nonexistent")
        assert limits.max_saved_strategies == 3

    def test_free_no_scanner(self):
        assert not can_access("free", "scanner")

    def test_pro_scanner(self):
        assert can_access("pro", "scanner")


# ── Integration Tests ────────────────────────────────────────────────────────

@pytest.fixture()
def app():
    from backend.api.main import create_app
    return create_app()


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_cookie(role: str) -> dict[str, str]:
    from backend.tests.conftest import make_access_token
    token = make_access_token(user_id=1, role=role)
    return {"access_token": token}


PAPER_POST_ENDPOINTS = [
    "/api/paper/reset/test",
    "/api/paper/halt/test",
    "/api/paper/resume/test",
]


@pytest.mark.parametrize("path", PAPER_POST_ENDPOINTS)
async def test_free_paper_trading_blocked(client, path):
    """Free plan kullanıcısı paper trading POST endpoint'lerine erişememeli (403)."""
    cookies = _make_cookie("free")
    resp = await client.post(path, json={}, cookies=cookies)
    assert resp.status_code == 403, f"POST {path} free → {resp.status_code}, beklenen 403"


@pytest.mark.parametrize("path", PAPER_POST_ENDPOINTS)
async def test_pro_paper_trading_allowed(client, path):
    """Pro plan kullanıcısı paper trading endpoint'lerine erişebilmeli."""
    cookies = _make_cookie("pro")
    resp = await client.post(path, json={}, cookies=cookies)
    # 403 olmamalı — 200 veya hata (strateji yok gibi) ama 403 değil
    assert resp.status_code != 403, f"POST {path} pro → {resp.status_code}, 403 olmamalı"

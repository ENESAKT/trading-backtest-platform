"""
test_billing.py — Billing router testleri.

STRIPE_SECRET_KEY yokken 503, token yokken 401 kontrolü.
"""

from __future__ import annotations

import os
import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.anyio


@pytest.fixture()
def app():
    # STRIPE_SECRET_KEY'i temizle — 503 senaryosunu test et
    os.environ.pop("STRIPE_SECRET_KEY", None)
    from backend.api.main import create_app
    return create_app()


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_cookie(role: str = "free") -> dict[str, str]:
    from backend.tests.conftest import make_access_token
    token = make_access_token(user_id=1, role=role)
    return {"access_token": token}


class TestBillingWithoutStripeKey:
    """STRIPE_SECRET_KEY yokken tüm billing endpoint'leri 503 döndürmeli."""

    async def test_checkout_503_without_stripe(self, client):
        cookies = _make_cookie("free")
        resp = await client.post(
            "/api/billing/checkout",
            json={"plan": "pro", "billing_period": "monthly"},
            cookies=cookies,
        )
        assert resp.status_code == 503

    async def test_portal_503_without_stripe(self, client):
        cookies = _make_cookie("pro")
        resp = await client.post("/api/billing/portal", cookies=cookies)
        assert resp.status_code == 503

    async def test_webhook_503_without_stripe(self, client):
        resp = await client.post(
            "/api/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "test"},
        )
        assert resp.status_code == 503


class TestBillingAuth:
    """Auth kontrolü — token'sız 401 dönmeli."""

    async def test_checkout_401_no_token(self, client):
        resp = await client.post(
            "/api/billing/checkout",
            json={"plan": "pro", "billing_period": "monthly"},
        )
        assert resp.status_code == 401

    async def test_portal_401_no_token(self, client):
        resp = await client.post("/api/billing/portal")
        assert resp.status_code == 401

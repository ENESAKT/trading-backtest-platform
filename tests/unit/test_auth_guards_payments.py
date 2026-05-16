from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.auth.dependencies import get_current_user, require_admin, require_backtest_pro
from backend.auth.jwt_utils import create_access_token


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/private")
    async def private(_: dict = Depends(get_current_user)) -> dict:
        return {"ok": True}

    @app.get("/admin")
    async def admin(_: dict = Depends(require_admin)) -> dict:
        return {"ok": True}

    @app.get("/backtest-pro")
    async def backtest_pro(_: dict = Depends(require_backtest_pro)) -> dict:
        return {"ok": True}

    return TestClient(app)


def _cookie(role: str = "free") -> dict[str, str]:
    return {"access_token": create_access_token(1, "user@example.com", role)}


def test_current_user_requires_access_cookie() -> None:
    resp = _client().get("/private")
    assert resp.status_code == 401
    assert resp.json()["detail"]["en"] == "Login required."


def test_admin_guard_blocks_non_admin_user() -> None:
    resp = _client().get("/admin", cookies=_cookie("pro"))
    assert resp.status_code == 403


def test_admin_guard_allows_admin_user() -> None:
    resp = _client().get("/admin", cookies=_cookie("admin"))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_backtest_pro_guard_blocks_free_and_allows_pro() -> None:
    assert _client().get("/backtest-pro", cookies=_cookie("free")).status_code == 403
    assert _client().get("/backtest-pro", cookies=_cookie("pro")).status_code == 200


def test_payments_webhook_uses_migration_backed_idempotency_table() -> None:
    source = "backend/api/payments_router.py"
    with open(source, encoding="utf-8") as fh:
        router_code = fh.read()
    assert "webhook_events" in router_code
    assert "stripe_events" not in router_code

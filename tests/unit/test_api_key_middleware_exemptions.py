"""API key middleware public market-data exemptions."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.middleware.api_key_auth import APIKeyMiddleware


async def _ok(_request):
    return JSONResponse({"ok": True})


def _client() -> TestClient:
    app = Starlette(
        routes=[
            Route("/api/v2/candles", _ok),
            Route("/api/market/chart", _ok),
            Route("/api/symbols", _ok),
            Route("/api/data/providers/health", _ok),
            Route("/api/auth/me", _ok),
            Route("/metrics", _ok),
        ],
        middleware=[Middleware(APIKeyMiddleware)],
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v2/candles?symbol=AKBNK.IS&interval=1d&limit=30",
        "/api/market/chart?symbol=AKBNK.IS&limit=30",
        "/api/symbols",
        "/api/data/providers/health",
        "/api/auth/me",
    ],
)
def test_browser_api_paths_ignore_api_key_when_api_glob_is_misconfigured(path: str) -> None:
    """Yanlış /api* ops konfigürasyonu browser API endpoint'lerini 401'e düşürmez."""
    env = dict(os.environ)
    env["API_KEY"] = "test-key-12345"
    env["API_KEY_PROTECTED_PATHS"] = "/api*,/metrics"
    with patch.dict(os.environ, env, clear=True):
        resp = _client().get(path)
        assert resp.status_code == 200, resp.text


def test_protected_ops_path_still_requires_api_key() -> None:
    """Public market-data muafiyeti /metrics korumasını gevşetmez."""
    env = dict(os.environ)
    env["API_KEY"] = "test-key-12345"
    env["API_KEY_PROTECTED_PATHS"] = "/api*,/metrics"
    with patch.dict(os.environ, env, clear=True):
        resp = _client().get("/metrics")
        assert resp.status_code == 401

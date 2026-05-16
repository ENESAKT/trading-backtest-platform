"""
PiyasaPilot backend test fixtures.

Ortak test bileşenleri: minimal app, auth token üretimi, httpx AsyncClient.
"""

from __future__ import annotations

import os
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

# Workers, harici DB, harici servisler test ortamında devre dışı
os.environ.setdefault("PIYASAPILOT_DISABLE_WORKERS", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_AUTH_DB", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_REDIS", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_DB_FACADE", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY", "1")
os.environ.setdefault("PIYASAPILOT_DISABLE_FINANCIAL_HARVEST", "1")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_unit_tests_only_min_64_chars_0123456789abcdef")


from backend.auth.jwt_utils import create_access_token


def make_access_token(
    user_id: int = 1,
    email: str = "test@piyasapilotu.com",
    role: str = "free",
) -> str:
    """Test amaçlı geçerli JWT access token üret."""
    return create_access_token(user_id, email, role)


@pytest.fixture()
def app():
    """Minimal FastAPI uygulama instance'ı döndürür."""
    from backend.api.main import create_app

    return create_app()


@pytest.fixture()
async def client(app):
    """httpx AsyncClient — her testte kullanılacak HTTP istemcisi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def auth_cookies() -> dict[str, str]:
    """Geçerli access_token cookie'si döndürür (free plan)."""
    token = make_access_token(user_id=1, role="free")
    return {"access_token": token}


@pytest.fixture()
def pro_cookies() -> dict[str, str]:
    """Pro plan cookie'si."""
    token = make_access_token(user_id=2, role="pro")
    return {"access_token": token}


@pytest.fixture()
def ultra_cookies() -> dict[str, str]:
    """Ultra plan cookie'si."""
    token = make_access_token(user_id=3, role="ultra")
    return {"access_token": token}


@pytest.fixture()
def admin_cookies() -> dict[str, str]:
    """Admin cookie'si."""
    token = make_access_token(user_id=4, role="admin")
    return {"access_token": token}

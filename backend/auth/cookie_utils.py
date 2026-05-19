"""
Secure + HttpOnly cookie yönetimi.
"""

from __future__ import annotations

import os

from fastapi import Response

COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", "")
IS_PRODUCTION: bool = os.environ.get("APP_ENV", "development") == "production"

ACCESS_COOKIE  = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int = 900,
    refresh_max_age: int = 604800,
) -> None:
    """Access + refresh token'ları güvenli cookie'lere yaz."""
    _set_cookie(response, ACCESS_COOKIE,  access_token,  max_age=access_max_age)
    _set_cookie(response, REFRESH_COOKIE, refresh_token, max_age=refresh_max_age)


def clear_auth_cookies(response: Response) -> None:
    """Her iki cookie'yi de sil."""
    response.delete_cookie(ACCESS_COOKIE,  domain=COOKIE_DOMAIN or None)
    response.delete_cookie(REFRESH_COOKIE, domain=COOKIE_DOMAIN or None)


def _set_cookie(
    response: Response,
    name: str,
    value: str,
    max_age: int,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        domain=COOKIE_DOMAIN if COOKIE_DOMAIN else None,
        path="/",
    )

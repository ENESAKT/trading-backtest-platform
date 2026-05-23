"""
Google OAuth2 akışı.
CSRF koruması: state parametresi Redis'te saklanır.
"""

from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx

from backend.config import getenv

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = "openid email profile"


def _is_real_value(value: str) -> bool:
    return bool(value and value.strip() and value.strip().lower() not in {"disabled", "none", "null", "false", "0", "buraya_yaz"})


def get_google_oauth_config() -> dict[str, str]:
    """Google OAuth ayarlarını .env yüklemesini garanti ederek oku."""
    return {
        "client_id": getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": getenv(
            "GOOGLE_REDIRECT_URI",
            "https://piyasapilot.com/api/auth/google/callback",
        ),
    }


def google_oauth_configured() -> bool:
    cfg = get_google_oauth_config()
    return _is_real_value(cfg["client_id"]) and _is_real_value(cfg["client_secret"])


def build_google_auth_url(state: str) -> str:
    """Google OAuth yönlendirme URL'si."""
    cfg = get_google_oauth_config()
    if not google_oauth_configured():
        raise RuntimeError("Google OAuth is not configured")
    params = {
        "client_id":     cfg["client_id"],
        "redirect_uri":  cfg["redirect_uri"],
        "response_type": "code",
        "scope":         SCOPES,
        "state":         state,
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    query = urlencode(params)
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Authorization code → access + id token."""
    cfg = get_google_oauth_config()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri":  cfg["redirect_uri"],
                "grant_type":    "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    """Google'dan kullanıcı bilgilerini al."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


# ── CSRF State (Redis) ───────────────────────────────────────────────────────

async def create_oauth_state(redis) -> str:
    """
    Rastgele state üret, Redis'e kaydet (5 dk TTL).
    redis: aioredis.Redis
    """
    state = secrets.token_urlsafe(32)
    await redis.setex(f"oauth:state:{state}", 300, "1")
    return state


async def verify_and_consume_state(redis, state: str) -> bool:
    """State'i doğrula ve Redis'ten sil (tek kullanım)."""
    key = f"oauth:state:{state}"
    val = await redis.get(key)
    if not val:
        return False
    await redis.delete(key)
    return True

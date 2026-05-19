"""
Google OAuth2 akışı.
CSRF koruması: state parametresi Redis'te saklanır.
"""

from __future__ import annotations

import os
import secrets

import httpx

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "https://piyasapilot.com/api/auth/google/callback",
)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = "openid email profile"


def build_google_auth_url(state: str) -> str:
    """Google OAuth yönlendirme URL'si."""
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
        "state":         state,
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Authorization code → access + id token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  GOOGLE_REDIRECT_URI,
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

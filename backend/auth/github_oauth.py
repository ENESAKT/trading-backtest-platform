"""GitHub OAuth2 akışı."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from backend.config import getenv

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
SCOPES = "read:user user:email"


def _is_real_value(value: str) -> bool:
    return bool(value and value.strip() and value.strip().lower() not in {"disabled", "none", "null", "false", "0", "buraya_yaz"})


def get_github_oauth_config() -> dict[str, str]:
    return {
        "client_id": getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": getenv("GITHUB_CLIENT_SECRET", ""),
        "redirect_uri": getenv(
            "GITHUB_REDIRECT_URI",
            "https://piyasapilot.com/api/auth/github/callback",
        ),
    }


def github_oauth_configured() -> bool:
    cfg = get_github_oauth_config()
    return _is_real_value(cfg["client_id"]) and _is_real_value(cfg["client_secret"])


def build_github_auth_url(state: str) -> str:
    cfg = get_github_oauth_config()
    if not github_oauth_configured():
        raise RuntimeError("GitHub OAuth is not configured")
    query = urlencode(
        {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "scope": SCOPES,
            "state": state,
            "allow_signup": "true",
        }
    )
    return f"{GITHUB_AUTH_URL}?{query}"


async def exchange_github_code_for_token(code: str) -> str:
    cfg = get_github_oauth_config()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": cfg["redirect_uri"],
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("GitHub OAuth token response did not include access_token")
        return token


async def get_github_user_info(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(GITHUB_USER_URL, headers=headers)
        user_resp.raise_for_status()
        user = user_resp.json()

        email = user.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_EMAILS_URL, headers=headers)
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            primary = next((item for item in emails if item.get("primary") and item.get("verified")), None)
            verified = primary or next((item for item in emails if item.get("verified")), None)
            email = verified.get("email") if verified else None

    if not email:
        raise RuntimeError("GitHub account does not expose a verified email")

    return {
        "id": str(user["id"]),
        "email": email,
        "name": user.get("name") or user.get("login") or email.split("@", 1)[0],
        "avatar_url": user.get("avatar_url"),
    }

"""
JWT access + refresh token yardımcıları.
"""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY: str       = os.environ.get("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_MIN_64_CHARS")
ALGORITHM: str        = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TTL: int       = int(os.environ.get("ACCESS_TOKEN_TTL_SECONDS",  "900"))     # 15 dk
REFRESH_TTL: int      = int(os.environ.get("REFRESH_TOKEN_TTL_SECONDS", "604800"))  # 7 gün


def create_access_token(user_id: int, email: str, role: str) -> str:
    """
    Kısa ömürlü access token (15 dk).
    sub = user_id (string)
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub":   str(user_id),
        "email": email,
        "role":  role,
        "jti":   str(uuid.uuid4()),
        "iat":   now,
        "exp":   now + timedelta(seconds=ACCESS_TTL),
        "type":  "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """
    Uzun ömürlü refresh token.
    Returns: (raw_token, token_hash) — raw DB'ye kaydedilmez, hash kaydedilir.
    """
    import hashlib
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, token_hash


def decode_access_token(token: str) -> dict:
    """
    Access token doğrula ve payload döndür.
    Geçersiz/süresi dolmuş → JWTError fırlatır.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Token türü geçersiz.")
    return payload


def hash_token(raw: str) -> str:
    """Herhangi bir token'ı SHA-256 ile hash'le (refresh + email verify vb.)"""
    import hashlib
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TTL)

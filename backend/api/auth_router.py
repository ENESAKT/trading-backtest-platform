"""
Auth Router — /api/auth/* endpoint'leri.
main.py'e:
    from backend.api.auth_router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from backend.auth.cookie_utils import clear_auth_cookies, set_auth_cookies
from backend.auth.dependencies import get_current_user
from backend.auth.email_sender import (
    send_password_reset_email,
    send_verification_email,
)
from backend.auth.feature_gate import get_limits
from backend.auth.google_oauth import (
    build_google_auth_url,
    create_oauth_state,
    exchange_code_for_tokens,
    get_google_user_info,
    verify_and_consume_state,
)
from backend.auth.jwt_utils import (
    ACCESS_TTL,
    REFRESH_TTL,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
)
from backend.auth.password import validate_password_strength, verify_password
from backend.auth.redis_store import AuthRedisStore
from backend.auth.repository import (
    consume_email_verification_token,
    consume_password_reset_token,
    create_email_verification_token,
    create_password_reset_token,
    create_user,
    get_or_create_oauth_user,
    get_refresh_token,
    get_user_by_email,
    get_user_by_id,
    get_user_settings,
    mark_email_verified,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
    update_last_login,
    update_password,
    update_user_settings,
)
from backend.auth.schemas import (
    ApiKeyCreateRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MobileLoginRequest,
    MobileRefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TotpVerifyRequest,
    UpdateSettingsRequest,
    VerifyEmailRequest,
)

router = APIRouter()

FRONTEND_URL = os.environ.get("PUBLIC_BASE_URL", "https://piyasapilotu.com")

# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _ok(data: dict | None = None) -> dict:
    return {"ok": True, "data": data or {}}


def _get_pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            503,
            detail={
                "tr": "Kimlik veritabanı hazır değil.",
                "en": "Auth database is not available.",
            },
        )
    return pool


def _get_redis(request: Request):
    return getattr(request.app.state, "redis", None)


async def _build_me_response(pool, user_id: int) -> dict:
    user = await get_user_by_id(pool, user_id)
    if not user:
        raise HTTPException(404, detail={"tr": "Kullanıcı bulunamadı.", "en": "User not found."})
    limits = get_limits(user["role"])
    settings = await get_user_settings(pool, user_id) or {}
    return {
        "id":             user["id"],
        "email":          user["email"],
        "email_verified": bool(user["email_verified"]),
        "display_name":   user.get("display_name"),
        "avatar_url":     user.get("avatar_url"),
        "role":           user["role"],
        "language":       user.get("language", "tr"),
        "plan": {
            "slug":                  user["role"],
            "backtest_pro":          limits.backtest_pro,
            "scanner":               limits.scanner,
            "real_time_data":        limits.real_time_data,
            "mali_analiz_scope":     limits.mali_analiz_scope,
            "multi_chart":           limits.multi_chart,
            "api_access":            limits.api_access,
            "max_watchlist_symbols": limits.max_watchlist_symbols,
            "backtest_runs_per_day": limits.backtest_runs_per_day,
            "api_calls_per_day":     limits.api_calls_per_day,
        },
        "settings": {
            "default_symbol":    settings.get("default_symbol", "BTCUSDT"),
            "default_timeframe": settings.get("default_timeframe", "1h"),
            "theme":             settings.get("theme", "dark"),
            "accent_color":      settings.get("accent_color", "amber"),
            "onboarding_done":   bool(settings.get("onboarding_done", False)),
            "language":          user.get("language", "tr"),
        },
    }


# ── Kayıt ────────────────────────────────────────────────────────────────────

@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    pool = _get_pool(request)

    password_errors = validate_password_strength(req.password)
    if password_errors:
        raise HTTPException(
            422,
            detail={"tr": " ".join(password_errors), "en": "Password does not meet security requirements."},
        )

    # Duplicate email kontrolü
    existing = await get_user_by_email(pool, req.email)
    if existing:
        raise HTTPException(
            409,
            detail={"tr": "Bu e-posta zaten kayıtlı.", "en": "Email already registered."},
        )

    user_id = await create_user(
        pool,
        email=req.email,
        password=req.password,
        display_name=req.display_name,
        email_verified=False,
    )

    # Email doğrulama gönder
    token = await create_email_verification_token(pool, user_id)
    send_verification_email(req.email, token, req.display_name)

    return _ok({"message": "Kayıt başarılı. E-posta doğrulama bağlantısı gönderildi.", "user_id": user_id})


# ── Giriş ────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    pool  = _get_pool(request)
    redis = _get_redis(request)

    # Brute-force koruması (Redis varsa)
    if redis:
        bf_key = f"login_fail:{req.email}"
        fails = await redis.get(bf_key)
        if fails and int(fails) >= 5:
            raise HTTPException(
                429,
                detail={"tr": "Çok fazla başarısız deneme. 30 dakika bekleyin.", "en": "Too many attempts. Wait 30 minutes."},
            )

    user = await get_user_by_email(pool, req.email)
    if not user or not user.get("password_hash"):
        if redis:
            await redis.incr(f"login_fail:{req.email}")
            await redis.expire(f"login_fail:{req.email}", 1800)
        raise HTTPException(
            401,
            detail={"tr": "E-posta veya şifre hatalı.", "en": "Invalid email or password."},
        )

    if not verify_password(req.password, user["password_hash"]):
        if redis:
            await redis.incr(f"login_fail:{req.email}")
            await redis.expire(f"login_fail:{req.email}", 1800)
        raise HTTPException(
            401,
            detail={"tr": "E-posta veya şifre hatalı.", "en": "Invalid email or password."},
        )

    if user.get("totp_enabled"):
        try:
            import pyotp
            valid_totp = bool(req.totp_code and pyotp.TOTP(user["totp_secret"]).verify(req.totp_code, valid_window=1))
        except Exception:
            valid_totp = False
        if not valid_totp:
            raise HTTPException(
                202,
                detail={"requires_2fa": True, "tr": "İki adımlı doğrulama kodu gerekli.", "en": "Two-factor code required."},
            )

    # Başarılı giriş — hata sayacını sıfırla
    if redis:
        await redis.delete(f"login_fail:{req.email}")

    access_token = create_access_token(user["id"], user["email"], user["role"])
    raw_refresh, refresh_hash = create_refresh_token()

    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    await store_refresh_token(pool, user["id"], refresh_hash, ua, ip)
    await update_last_login(pool, user["id"])

    set_auth_cookies(response, access_token, raw_refresh, ACCESS_TTL, REFRESH_TTL)

    me = await _build_me_response(pool, user["id"])
    return _ok(me)


@router.post("/mobile/login")
async def mobile_login(req: MobileLoginRequest, request: Request):
    """Mobil istemciler için cookie yerine Bearer access + refresh token döndür."""
    pool = _get_pool(request)

    user = await get_user_by_email(pool, req.email)
    if not user or not user.get("password_hash") or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            401,
            detail={"tr": "E-posta veya şifre hatalı.", "en": "Invalid email or password."},
        )

    if user.get("totp_enabled"):
        try:
            import pyotp
            valid_totp = bool(req.totp_code and pyotp.TOTP(user["totp_secret"]).verify(req.totp_code, valid_window=1))
        except Exception:
            valid_totp = False
        if not valid_totp:
            raise HTTPException(
                202,
                detail={"requires_2fa": True, "tr": "İki adımlı doğrulama kodu gerekli.", "en": "Two-factor code required."},
            )

    access_token = create_access_token(user["id"], user["email"], user["role"])
    raw_refresh, refresh_hash = create_refresh_token()
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    await store_refresh_token(pool, user["id"], refresh_hash, ua, ip, req.device_name or "mobile")
    await update_last_login(pool, user["id"])

    return _ok({
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "Bearer",
        "expires_in": ACCESS_TTL,
        "user": await _build_me_response(pool, user["id"]),
    })


# ── Çıkış ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request, response: Response):
    pool = _get_pool(request)
    redis = _get_redis(request)
    access = request.cookies.get("access_token")
    if redis and access:
        try:
            payload = decode_access_token(access)
            await AuthRedisStore(redis).block_token(payload.get("jti", ""), ACCESS_TTL)
        except Exception:
            pass
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        token_hash = hash_token(raw_refresh)
        await revoke_refresh_token(pool, token_hash)
    clear_auth_cookies(response)
    return _ok({"message": "Çıkış yapıldı."})


# ── Token Yenileme ────────────────────────────────────────────────────────────

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    pool = _get_pool(request)
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(401, detail={"tr": "Oturum bulunamadı.", "en": "No session found."})

    token_hash = hash_token(raw_refresh)
    rt = await get_refresh_token(pool, token_hash)
    if not rt:
        clear_auth_cookies(response)
        raise HTTPException(401, detail={"tr": "Oturum süresi doldu.", "en": "Session expired."})

    user = await get_user_by_id(pool, rt["user_id"])
    if not user:
        raise HTTPException(401, detail={"tr": "Kullanıcı bulunamadı.", "en": "User not found."})

    # Eski token'ı iptal et, yenisini üret (rotation)
    await revoke_refresh_token(pool, token_hash)
    new_access = create_access_token(user["id"], user["email"], user["role"])
    new_raw, new_hash = create_refresh_token()
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    await store_refresh_token(pool, user["id"], new_hash, ua, ip)

    set_auth_cookies(response, new_access, new_raw, ACCESS_TTL, REFRESH_TTL)
    return _ok({"message": "Token yenilendi."})


@router.post("/mobile/refresh")
async def mobile_refresh(req: MobileRefreshRequest, request: Request):
    """Mobil refresh token rotation. Cookie kullanmaz, JSON body ile çalışır."""
    pool = _get_pool(request)
    token_hash = hash_token(req.refresh_token)
    rt = await get_refresh_token(pool, token_hash)
    if not rt:
        raise HTTPException(401, detail={"tr": "Oturum süresi doldu.", "en": "Session expired."})

    user = await get_user_by_id(pool, rt["user_id"])
    if not user:
        raise HTTPException(401, detail={"tr": "Kullanıcı bulunamadı.", "en": "User not found."})

    await revoke_refresh_token(pool, token_hash)
    access_token = create_access_token(user["id"], user["email"], user["role"])
    raw_refresh, refresh_hash = create_refresh_token()
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    await store_refresh_token(pool, user["id"], refresh_hash, ua, ip, req.device_name or "mobile")

    return _ok({
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "Bearer",
        "expires_in": ACCESS_TTL,
    })


# ── Mevcut Kullanıcı ─────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    me = await _build_me_response(pool, int(user["sub"]))
    return _ok(me)


@router.get("/me/limits")
async def get_me_limits(request: Request, user: dict = Depends(get_current_user)):
    """Kullanıcının plan limitleri ve günlük kullanımı.
    Frontend bu endpoint'i kullanarak backtest kotasını gösterebilir.
    """
    from backend.auth.feature_gate import get_limits
    pool = _get_pool(request)
    db_user = await get_user_by_id(pool, int(user["sub"]))
    if not db_user:
        raise HTTPException(404, detail={"tr": "Kullanıcı bulunamadı."})
    limits = get_limits(db_user["role"])
    return _ok({
        "role": db_user["role"],
        "backtest_runs_per_day": limits.backtest_runs_per_day,
        "api_calls_per_day":     limits.api_calls_per_day,
        "max_watchlist_symbols": limits.max_watchlist_symbols,
        "backtest_pro":          limits.backtest_pro,
        "scanner":               limits.scanner,
        "real_time_data":        limits.real_time_data,
        "mali_analiz_scope":     limits.mali_analiz_scope,
        "multi_chart":           limits.multi_chart,
        "api_access":            limits.api_access,
    })


@router.patch("/me/settings")
async def update_settings(
    req: UpdateSettingsRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    pool = _get_pool(request)
    updates: dict = {}
    if req.default_symbol is not None:
        updates["default_symbol"] = req.default_symbol
    if req.default_timeframe is not None:
        updates["default_timeframe"] = req.default_timeframe
    if req.theme is not None:
        updates["theme"] = req.theme
    if req.accent_color is not None:
        updates["accent_color"] = req.accent_color
    if req.onboarding_done is not None:
        updates["onboarding_done"] = req.onboarding_done
    await update_user_settings(pool, int(user["sub"]), updates)
    return _ok({"message": "Ayarlar güncellendi."})


# ── Email Doğrulama ──────────────────────────────────────────────────────────

@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, request: Request):
    pool = _get_pool(request)
    user_id = await consume_email_verification_token(pool, req.token)
    if not user_id:
        raise HTTPException(400, detail={"tr": "Geçersiz veya süresi dolmuş token.", "en": "Invalid or expired token."})
    await mark_email_verified(pool, user_id)
    return _ok({"message": "E-posta doğrulandı."})


@router.post("/resend-verification")
async def resend_verification(request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    u = await get_user_by_id(pool, int(user["sub"]))
    if u and u.get("email_verified"):
        return _ok({"message": "E-posta zaten doğrulanmış."})
    token = await create_email_verification_token(pool, int(user["sub"]))
    send_verification_email(u["email"], token, u.get("display_name", ""))
    return _ok({"message": "Doğrulama e-postası yeniden gönderildi."})


# ── Şifre Sıfırlama ──────────────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, request: Request):
    pool = _get_pool(request)
    user = await get_user_by_email(pool, req.email)
    # Kullanıcı yoksa da başarı döndür — email enumeration önleme
    if user and user.get("password_hash"):
        token = await create_password_reset_token(pool, user["id"])
        send_password_reset_email(req.email, token)
    return _ok({"message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."})


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, request: Request):
    pool = _get_pool(request)
    user_id = await consume_password_reset_token(pool, req.token)
    if not user_id:
        raise HTTPException(400, detail={"tr": "Geçersiz veya süresi dolmuş token.", "en": "Invalid or expired token."})
    await update_password(pool, user_id, req.new_password)
    await revoke_all_user_tokens(pool, user_id)   # tüm oturumları kapat
    return _ok({"message": "Şifreniz güncellendi. Lütfen tekrar giriş yapın."})


# ── Google OAuth ─────────────────────────────────────────────────────────────

@router.get("/google")
async def google_auth(request: Request):
    redis = _get_redis(request)
    if not redis:
        raise HTTPException(503, detail={"tr": "OAuth state deposu hazır değil.", "en": "OAuth state store is unavailable."})
    state = await create_oauth_state(redis)
    url = build_google_auth_url(state)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
):
    pool  = _get_pool(request)
    redis = _get_redis(request)

    # CSRF state kontrolü
    if not redis:
        raise HTTPException(503, detail={"tr": "OAuth state deposu hazır değil.", "en": "OAuth state store is unavailable."})
    valid = await verify_and_consume_state(redis, state)
    if not valid:
        raise HTTPException(400, detail={"tr": "Geçersiz OAuth state.", "en": "Invalid OAuth state."})

    # Google'dan token al
    try:
        tokens      = await exchange_code_for_tokens(code)
        google_user = await get_google_user_info(tokens["access_token"])
    except Exception:
        raise HTTPException(400, detail={"tr": "Google ile giriş başarısız.", "en": "Google authentication failed."})

    user_id, is_new = await get_or_create_oauth_user(
        pool,
        provider="google",
        provider_user_id=google_user["sub"],
        email=google_user["email"],
        display_name=google_user.get("name", ""),
        avatar_url=google_user.get("picture"),
    )

    user = await get_user_by_id(pool, user_id)
    await update_last_login(pool, user_id)

    access_token = create_access_token(user_id, user["email"], user["role"])
    raw_refresh, refresh_hash = create_refresh_token()
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    await store_refresh_token(pool, user_id, refresh_hash, ua, ip)

    set_auth_cookies(response, access_token, raw_refresh, ACCESS_TTL, REFRESH_TTL)

    # Yeni kullanıcıyı onboarding'e, eskisini app'e yönlendir
    redirect_to = f"{FRONTEND_URL}/onboarding" if is_new else f"{FRONTEND_URL}/app"
    return RedirectResponse(redirect_to)


# ── Aktif Oturumlar ──────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT id, user_agent, ip_address, device_name, created_at, expires_at
                   FROM refresh_tokens
                   WHERE user_id = %s AND revoked_at IS NULL AND expires_at > NOW()
                   ORDER BY created_at DESC""",
                (int(user["sub"]),),
            )
            rows = await cur.fetchall()
    sessions = [
        {
            "id":          r[0],
            "user_agent":  r[1],
            "ip_address":  r[2],
            "device_name": r[3],
            "created_at":  str(r[4]),
            "expires_at":  str(r[5]),
        }
        for r in rows
    ]
    return _ok({"sessions": sessions})


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    request: Request,
    user: dict = Depends(get_current_user),
):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = %s AND user_id = %s",
                (session_id, int(user["sub"])),
            )
            await conn.commit()
    return _ok({"message": "Oturum kapatıldı."})


# ── 2FA / TOTP ────────────────────────────────────────────────────────────────

@router.get("/2fa/setup")
async def setup_2fa(request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    import pyotp
    secret = pyotp.random_base32()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET totp_secret=%s, totp_enabled=FALSE WHERE id=%s", (secret, int(user["sub"])))
            await conn.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.get("email", ""), issuer_name="PiyasaPilot")
    return _ok({"secret": secret, "provisioning_uri": uri})


@router.post("/2fa/verify")
async def verify_2fa(req: TotpVerifyRequest, request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    u = await get_user_by_id(pool, int(user["sub"]))
    if not u or not u.get("totp_secret"):
        raise HTTPException(400, detail={"tr": "2FA kurulumu bulunamadı.", "en": "2FA setup not found."})
    import pyotp
    if not pyotp.TOTP(u["totp_secret"]).verify(req.code, valid_window=1):
        raise HTTPException(400, detail={"tr": "Kod hatalı.", "en": "Invalid code."})
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET totp_enabled=TRUE WHERE id=%s", (int(user["sub"]),))
            await conn.commit()
    return _ok({"message": "2FA aktif edildi."})


@router.post("/2fa/disable")
async def disable_2fa(req: TotpVerifyRequest, request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    u = await get_user_by_id(pool, int(user["sub"]))
    if not u or not u.get("totp_enabled"):
        return _ok({"message": "2FA zaten kapalı."})
    import pyotp
    if not pyotp.TOTP(u["totp_secret"]).verify(req.code, valid_window=1):
        raise HTTPException(400, detail={"tr": "Kod hatalı.", "en": "Invalid code."})
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET totp_enabled=FALSE, totp_secret=NULL WHERE id=%s", (int(user["sub"]),))
            await conn.commit()
    return _ok({"message": "2FA kapatıldı."})


# ── API Keys (Ultra) ─────────────────────────────────────────────────────────

@router.get("/api-keys")
async def list_api_keys(request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, last_used, expires_at, created_at FROM api_keys WHERE user_id=%s ORDER BY created_at DESC", (int(user["sub"]),))
            rows = await cur.fetchall()
    return _ok({"keys": [
        {"id": r[0], "name": r[1], "last_used": str(r[2]) if r[2] else None, "expires_at": str(r[3]) if r[3] else None, "created_at": str(r[4])}
        for r in rows
    ]})


@router.post("/api-keys")
async def create_api_key(req: ApiKeyCreateRequest, request: Request, user: dict = Depends(get_current_user)):
    if user.get("role") not in {"ultra", "admin"}:
        raise HTTPException(403, detail={"tr": "API erişimi Ultra planı gerektirir.", "en": "API access requires Ultra."})
    import secrets
    raw = "pp_" + secrets.token_urlsafe(32)
    key_hash = hash_token(raw)
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO api_keys (user_id, name, key_hash, expires_at) VALUES (%s, %s, %s, %s)",
                (int(user["sub"]), req.name, key_hash, req.expires_at),
            )
            await conn.commit()
            await cur.execute("SELECT LAST_INSERT_ID()")
            key_id = (await cur.fetchone())[0]
    return _ok({"id": key_id, "api_key": raw, "warning": "Bu anahtar yalnızca bir kez gösterilir."})


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, request: Request, user: dict = Depends(get_current_user)):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM api_keys WHERE id=%s AND user_id=%s", (key_id, int(user["sub"])))
            await conn.commit()
    return _ok({"deleted": key_id})

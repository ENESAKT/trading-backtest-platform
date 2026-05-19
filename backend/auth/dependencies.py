"""
FastAPI bağımlılıkları — auth guard'lar.

Kullanım:
    @router.get("/...", dependencies=[Depends(require_backtest_pro)])

    @router.post("/...")
    async def my_endpoint(user = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

from datetime import date

from fastapi import Depends, HTTPException, Request
from jose import JWTError

from .feature_gate import can_access, get_quota
from .jwt_utils import decode_access_token
from .redis_store import AuthRedisStore

# ── Temel Bağımlılıklar ──────────────────────────────────────────────────────

async def get_current_user(request: Request) -> dict:
    """
    Cookie veya Authorization Bearer header'dan access token oku, doğrula, user payload döndür.
    Geçersiz / eksik token → 401
    """
    token = request.cookies.get("access_token")
    auth_header = request.headers.get("authorization", "")
    if not token and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"tr": "Giriş yapınız.", "en": "Login required."},
        )
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"tr": "Oturum süresi doldu. Lütfen tekrar giriş yapın.", "en": "Session expired."},
        )
    redis = getattr(request.app.state, "redis", None)
    if redis is not None and await AuthRedisStore(redis).is_token_blocked(payload.get("jti", "")):
        raise HTTPException(401, detail={"tr": "Oturum iptal edildi.", "en": "Session revoked."})
    pool = getattr(request.app.state, "db_pool", None)
    if pool is not None:
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT is_active FROM users WHERE id=%s", (int(payload["sub"]),))
                    row = await cur.fetchone()
                    if not row or not row[0]:
                        raise HTTPException(401, detail={"tr": "Hesap pasif.", "en": "Account disabled."})
        except HTTPException:
            raise
        except Exception:
            pass
    return payload


async def get_optional_user(request: Request) -> dict | None:
    """
    Cookie veya Bearer token varsa doğrula, yoksa None döndür.
    Misafir sayfaları için kullanılır.
    """
    token = request.cookies.get("access_token")
    auth_header = request.headers.get("authorization", "")
    if not token and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return decode_access_token(token)
    except JWTError:
        return None


# ── Rol Kontrolleri ──────────────────────────────────────────────────────────

def require_role(*roles: str):
    """Belirtilen rollerden birine sahip olmayı zorunlu kılar."""
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "tr": "Bu sayfaya erişim yetkiniz yok.",
                    "en": "Access denied.",
                },
            )
        return user
    return checker


# ── Özellik Kontrolleri ──────────────────────────────────────────────────────

def require_feature(feature: str):
    """Özellik erişim kontrolü — PlanLimits üzerinden."""
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        role = user.get("role", "free")
        if not can_access(role, feature):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PLAN_LIMIT",
                    "tr": "Bu özellik Pro veya Ultra planında mevcut.",
                    "en": "This feature requires a Pro or Ultra plan.",
                    "upgrade_url": "https://piyasapilot.com/pricing",
                },
            )
        return user
    return checker


# ── Kota Kontrolleri ─────────────────────────────────────────────────────────

async def _get_daily_usage(app_state, user_id: int, field: str) -> int:
    """
    MySQL'den bugünkü kullanım sayısını oku.
    app_state.db_pool: aiomysql.Pool
    """
    today = date.today().isoformat()
    col_map = {
        "backtest_runs_per_day": "backtest_runs",
        "signals_per_day":       "signal_views",
        "api_calls_per_day":     "api_calls",
    }
    col = col_map.get(field, field)
    try:
        async with app_state.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {col} FROM daily_usage WHERE user_id=%s AND date=%s",
                    (user_id, today),
                )
                row = await cur.fetchone()
                return row[0] if row else 0
    except Exception:
        return 0  # DB hatasında engelleme yapma


async def _increment_daily_usage(app_state, user_id: int, field: str) -> None:
    """Günlük sayacı artır (INSERT ... ON DUPLICATE KEY UPDATE)."""
    today = date.today().isoformat()
    col_map = {
        "backtest_runs_per_day": "backtest_runs",
        "signals_per_day":       "signal_views",
        "api_calls_per_day":     "api_calls",
    }
    col = col_map.get(field, field)
    try:
        async with app_state.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""INSERT INTO daily_usage (user_id, date, {col})
                        VALUES (%s, %s, 1)
                        ON DUPLICATE KEY UPDATE {col} = {col} + 1""",
                    (user_id, today),
                )
                await conn.commit()
    except Exception:
        pass


def require_quota(counter_field: str):
    """Günlük kota kontrolü + sayacı artır."""
    async def checker(
        request: Request,
        user: dict = Depends(get_current_user),
    ) -> dict:
        role = user.get("role", "free")
        limit = get_quota(role, counter_field)

        if limit == -1:          # sınırsız
            return user

        user_id = int(user["sub"])
        used = await _get_daily_usage(request.app.state, user_id, counter_field)

        if used >= limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "tr": "Günlük kotanız doldu. Yarın yenilenir veya planı yükseltin.",
                    "en": "Daily quota exceeded. Resets tomorrow or upgrade your plan.",
                    "limit":        limit,
                    "used":         used,
                    "upgrade_url":  "https://piyasapilot.com/pricing",
                },
            )

        # Sayacı artır (fire-and-forget tarzı)
        await _increment_daily_usage(request.app.state, user_id, counter_field)
        return user
    return checker


# ── Hazır Kısayollar ─────────────────────────────────────────────────────────

require_admin          = require_role("admin")
require_pro            = require_role("pro", "ultra", "admin")
require_ultra          = require_role("ultra", "admin")
require_backtest_pro   = require_feature("backtest_pro")
require_scanner        = require_feature("scanner")
require_realtime       = require_feature("real_time_data")
require_api_access     = require_feature("api_access")
require_multi_chart    = require_feature("multi_chart")
require_paper_trading  = require_feature("paper_trading")

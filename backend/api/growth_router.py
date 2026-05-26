"""Growth API — waitlist, referrals and public backtest sharing.

Referral sistemi:
  - Her kullanıcı için benzersiz 8 karakterlik kod otomatik oluşturulur.
  - /api/r/{code} tıklandığında referral_events tablosuna click kaydedilir.
  - Yeni kayıt sırasında ref_code query parametresi geçilirse conversion kaydedilir.
  - Ödül mantığı: 3 başarılı conversion → referred_by kullanıcısına "pro_trial_7d" ödülü.
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr

router = APIRouter()

# ─── Sabitle ────────────────────────────────────────────────────────────────

_CODE_ALPHABET = string.ascii_uppercase + string.digits  # 36 karakter, O/0 dahil (hızlı)
_CODE_LENGTH   = 8
_REWARD_THRESHOLD = 3        # kaç conversion sonrası ödül verilir
_REWARD_TYPE      = "pro_trial_7d"

# ─── Pydantic şemalar ────────────────────────────────────────────────────────

class WaitlistRequest(BaseModel):
    email: EmailStr
    source: Optional[str] = None
    ref_code: Optional[str] = None   # varsa hangi referral kodundan geldi


class ShareBacktestRequest(BaseModel):
    backtest_id: str
    is_public: bool = True


class ReferralCodeResponse(BaseModel):
    code: str
    url: str
    total_clicks: int
    total_conversions: int
    pending_reward: bool


# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def _ok(data: dict | None = None) -> dict:
    return {"ok": True, "data": data or {}}


def _get_pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            503,
            detail={"tr": "Büyüme veritabanı hazır değil.", "en": "Growth database is unavailable."},
        )
    return pool


def _generate_code() -> str:
    """8 karakterlik URL-safe referral kodu üretir."""
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


async def _get_or_create_referral_code(conn, user_id: int) -> str:
    """Kullanıcının mevcut kodunu döndürür; yoksa yeni oluşturup kaydeder."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT code FROM referral_codes WHERE user_id = %s LIMIT 1",
            (user_id,),
        )
        row = await cur.fetchone()
        if row:
            return row[0]

        # Benzersiz kod üret (çakışma ihtimali çok düşük ama kontrol edilir)
        for _ in range(10):
            code = _generate_code()
            await cur.execute(
                "SELECT 1 FROM referral_codes WHERE code = %s LIMIT 1", (code,)
            )
            if not await cur.fetchone():
                break
        else:
            raise HTTPException(500, detail="Referral kodu üretilemedi.")

        await cur.execute(
            "INSERT INTO referral_codes (user_id, code, created_at) VALUES (%s, %s, %s)",
            (user_id, code, datetime.now(timezone.utc)),
        )
        await conn.commit()
        return code


async def _record_conversion(conn, code: str) -> None:
    """
    Referral conversion kaydeder ve eşik aşıldıysa ödül satırı oluşturur.
    Ödül zaten verilmişse tekrar vermez (idempotent).
    """
    async with conn.cursor() as cur:
        # Kod sahibini bul
        await cur.execute(
            "SELECT user_id FROM referral_codes WHERE code = %s LIMIT 1", (code,)
        )
        row = await cur.fetchone()
        if not row:
            return
        referrer_user_id = row[0]

        # Conversion sayısını artır
        await cur.execute(
            """INSERT INTO referral_events (code, event_type, created_at)
               VALUES (%s, 'conversion', %s)""",
            (code, datetime.now(timezone.utc)),
        )

        # Toplam conversion sayısını hesapla
        await cur.execute(
            "SELECT COUNT(*) FROM referral_events WHERE code = %s AND event_type = 'conversion'",
            (code,),
        )
        total_conversions = (await cur.fetchone())[0]

        # Eşik aşıldıysa ödül ver (henüz verilmemişse)
        if total_conversions >= _REWARD_THRESHOLD:
            await cur.execute(
                """SELECT 1 FROM referral_rewards
                   WHERE user_id = %s AND reward_type = %s AND code = %s
                   LIMIT 1""",
                (referrer_user_id, _REWARD_TYPE, code),
            )
            already_rewarded = await cur.fetchone()
            if not already_rewarded:
                await cur.execute(
                    """INSERT INTO referral_rewards
                       (user_id, code, reward_type, granted_at)
                       VALUES (%s, %s, %s, %s)""",
                    (referrer_user_id, code, _REWARD_TYPE, datetime.now(timezone.utc)),
                )

        await conn.commit()


# ─── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.post("/waitlist")
async def join_waitlist(req: WaitlistRequest, request: Request):
    """Bekleme listesine kayıt. Opsiyonel referral kodu desteklenir."""
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO waitlist (email, source, ref_code, joined_at)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                     source   = VALUES(source),
                     ref_code = COALESCE(ref_code, VALUES(ref_code))""",
                (req.email, req.source or "web", req.ref_code, datetime.now(timezone.utc)),
            )
            await cur.execute("SELECT COUNT(*) FROM waitlist")
            count = (await cur.fetchone())[0]
            await conn.commit()

        # Referral conversion kaydı
        if req.ref_code:
            await _record_conversion(conn, req.ref_code.upper())

    return _ok({"count": count})


@router.get("/r/{code}")
async def referral_redirect(code: str, request: Request):
    """
    Referral link tıklamasını kaydeder ve kayıt sayfasına yönlendirir.
    Gerçek HTTP redirect yerine JSON döner — frontend yönlendirmeyi yapar.
    """
    upper_code = code.upper()
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Kodun varlığını kontrol et
            await cur.execute(
                "SELECT 1 FROM referral_codes WHERE code = %s LIMIT 1", (upper_code,)
            )
            if not await cur.fetchone():
                # Geçersiz kod — yine de yönlendir ama event kaydetme
                return _ok({"redirect_to": "/register", "valid": False})

            # Click event kaydet
            await cur.execute(
                """INSERT INTO referral_events (code, event_type, created_at)
                   VALUES (%s, 'click', %s)""",
                (upper_code, datetime.now(timezone.utc)),
            )
            await conn.commit()

    return _ok({
        "redirect_to": f"/register?ref={upper_code}",
        "valid": True,
    })


@router.post("/referral/code")
async def get_my_referral_code(request: Request):
    """
    Oturum açmış kullanıcının referral kodunu döndürür.
    Yoksa otomatik oluşturur.
    Requires: Bearer token (X-User-Id header set by auth middleware).
    """
    user_id_raw = request.headers.get("X-User-Id")
    if not user_id_raw:
        raise HTTPException(401, detail={"tr": "Giriş gerekli.", "en": "Authentication required."})
    try:
        user_id = int(user_id_raw)
    except ValueError:
        raise HTTPException(400, detail="Geçersiz kullanıcı ID.")

    pool = _get_pool(request)
    base_url = str(request.base_url).rstrip("/")

    async with pool.acquire() as conn:
        code = await _get_or_create_referral_code(conn, user_id)
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM referral_events WHERE code = %s AND event_type = 'click'",
                (code,),
            )
            total_clicks = (await cur.fetchone())[0]

            await cur.execute(
                "SELECT COUNT(*) FROM referral_events WHERE code = %s AND event_type = 'conversion'",
                (code,),
            )
            total_conversions = (await cur.fetchone())[0]

            await cur.execute(
                "SELECT 1 FROM referral_rewards WHERE user_id = %s AND reward_type = %s LIMIT 1",
                (user_id, _REWARD_TYPE),
            )
            pending_reward = bool(await cur.fetchone()) and total_conversions < _REWARD_THRESHOLD

    return _ok(ReferralCodeResponse(
        code=code,
        url=f"{base_url}/api/r/{code}",
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        pending_reward=total_conversions >= _REWARD_THRESHOLD,
    ).model_dump())


@router.get("/referral/stats")
async def get_referral_stats(
    request: Request,
    code: Optional[str] = Query(None, description="Belirli bir kodu sorgula (admin)"),
):
    """
    Referral istatistiklerini döndürür.
    code query parametresi verilirse o koda ait stats getirilir.
    Verilmezse X-User-Id başlığındaki kullanıcının kodu kullanılır.
    """
    pool = _get_pool(request)

    if code:
        lookup_code = code.upper()
    else:
        user_id_raw = request.headers.get("X-User-Id")
        if not user_id_raw:
            raise HTTPException(401, detail={"tr": "Giriş gerekli.", "en": "Authentication required."})
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT code FROM referral_codes WHERE user_id = %s LIMIT 1",
                    (int(user_id_raw),),
                )
                row = await cur.fetchone()
        if not row:
            return _ok({"code": None, "clicks": 0, "conversions": 0, "rewards": 0})
        lookup_code = row[0]

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT event_type, COUNT(*) FROM referral_events WHERE code = %s GROUP BY event_type",
                (lookup_code,),
            )
            rows = await cur.fetchall()
            events = {r[0]: r[1] for r in rows}

            await cur.execute(
                "SELECT COUNT(*) FROM referral_rewards WHERE code = %s", (lookup_code,)
            )
            reward_count = (await cur.fetchone())[0]

    return _ok({
        "code": lookup_code,
        "clicks": events.get("click", 0),
        "conversions": events.get("conversion", 0),
        "rewards_granted": reward_count,
        "next_reward_at": max(0, _REWARD_THRESHOLD - events.get("conversion", 0)),
    })


@router.post("/backtest/share")
async def share_backtest(req: ShareBacktestRequest, request: Request):
    pool = _get_pool(request)
    slug = secrets.token_urlsafe(8).replace("_", "").replace("-", "")[:10]
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO public_backtests (run_id, public_slug, is_public)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE is_public=VALUES(is_public)""",
                (req.backtest_id, slug, req.is_public),
            )
            await cur.execute("SELECT public_slug FROM public_backtests WHERE run_id=%s", (req.backtest_id,))
            row = await cur.fetchone()
            await conn.commit()
    public_slug = row[0] if row else slug
    base_url = str(request.base_url).rstrip("/")
    return _ok({"url": f"{base_url}/shared/{public_slug}", "slug": public_slug})


@router.get("/shared/{slug}")
async def get_shared_backtest(slug: str, request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT run_id FROM public_backtests WHERE public_slug=%s AND is_public=TRUE",
                (slug,),
            )
            row = await cur.fetchone()
    if not row:
        raise HTTPException(404, detail={"tr": "Paylaşım bulunamadı.", "en": "Share not found."})
    return _ok({"run_id": row[0]})

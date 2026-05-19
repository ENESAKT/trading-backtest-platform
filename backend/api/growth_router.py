"""Growth API — waitlist, referrals and public backtest sharing."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

router = APIRouter()


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str | None = None


class ShareBacktestRequest(BaseModel):
    backtest_id: str
    is_public: bool = True


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


@router.post("/waitlist")
async def join_waitlist(req: WaitlistRequest, request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO waitlist (email, source)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE source=VALUES(source)""",
                (req.email, req.source or "web"),
            )
            await cur.execute("SELECT COUNT(*) FROM waitlist")
            count = (await cur.fetchone())[0]
            await conn.commit()
    return _ok({"count": count})


@router.get("/r/{code}")
async def referral_redirect(code: str):
    return {"ok": True, "redirect_to": f"/register?ref={code.upper()}"}


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

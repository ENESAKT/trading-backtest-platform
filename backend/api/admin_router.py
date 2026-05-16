"""Admin API — user/subscription/audit management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import require_admin
from backend.auth.repository import revoke_all_user_tokens

router = APIRouter(dependencies=[Depends(require_admin)])


class RoleUpdateRequest(BaseModel):
    role: str


def _ok(data: dict | None = None) -> dict:
    return {"ok": True, "data": data or {}}


def _get_pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, detail={"tr": "Admin veritabanı hazır değil.", "en": "Admin database is not available."})
    return pool


@router.get("/users")
async def list_users(request: Request, q: str = "", role: str = "", active: str = "", limit: int = 50, offset: int = 0):
    pool = _get_pool(request)
    clauses = ["1=1"]
    params: list[object] = []
    if q:
        clauses.append("email LIKE %s")
        params.append(f"%{q}%")
    if role:
        clauses.append("role = %s")
        params.append(role)
    if active in {"true", "false"}:
        clauses.append("is_active = %s")
        params.append(active == "true")
    params.extend([max(1, min(limit, 200)), max(0, offset)])
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""SELECT id, email, email_verified, display_name, role, is_active,
                           last_login_at, created_at
                    FROM users
                    WHERE {' AND '.join(clauses)}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s""",
                params,
            )
            rows = await cur.fetchall()
    users = [
        {
            "id": r[0],
            "email": r[1],
            "email_verified": bool(r[2]),
            "display_name": r[3],
            "role": r[4],
            "is_active": bool(r[5]),
            "last_login_at": str(r[6]) if r[6] else None,
            "created_at": str(r[7]) if r[7] else None,
        }
        for r in rows
    ]
    return _ok({"users": users, "total": len(users), "limit": max(1, min(limit, 200)), "offset": max(0, offset)})


@router.get("/overview")
async def overview(request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*), SUM(role='pro'), SUM(role='ultra'), SUM(is_active=TRUE) FROM users")
            user_row = await cur.fetchone()
            await cur.execute("SELECT COUNT(*) FROM refresh_tokens WHERE revoked_at IS NULL AND expires_at > NOW()")
            sessions = (await cur.fetchone())[0]
            await cur.execute(
                """SELECT COUNT(*), SUM(status IN ('trialing','active')), SUM(status='past_due')
                   FROM user_subscriptions"""
            )
            sub_row = await cur.fetchone()
    return _ok({
        "users_total": int(user_row[0] or 0),
        "pro_users": int(user_row[1] or 0),
        "ultra_users": int(user_row[2] or 0),
        "active_users": int(user_row[3] or 0),
        "active_sessions": int(sessions or 0),
        "subscriptions_total": int(sub_row[0] or 0),
        "subscriptions_active": int(sub_row[1] or 0),
        "subscriptions_past_due": int(sub_row[2] or 0),
    })


@router.get("/subscriptions")
async def subscriptions(request: Request, limit: int = 50):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT us.id, u.email, sp.slug, us.billing_period, us.status,
                          us.current_period_end, us.stripe_subscription_id
                   FROM user_subscriptions us
                   JOIN users u ON u.id = us.user_id
                   JOIN subscription_plans sp ON sp.id = us.plan_id
                   ORDER BY us.created_at DESC
                   LIMIT %s""",
                (max(1, min(limit, 200)),),
            )
            rows = await cur.fetchall()
    return _ok({"subscriptions": [
        {
            "id": r[0],
            "email": r[1],
            "plan": r[2],
            "billing_period": r[3],
            "status": r[4],
            "current_period_end": str(r[5]) if r[5] else None,
            "stripe_subscription_id": r[6],
        }
        for r in rows
    ]})


@router.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, email, email_verified, display_name, role, is_active, last_login_at, created_at FROM users WHERE id=%s", (user_id,))
            row = await cur.fetchone()
    if not row:
        raise HTTPException(404, detail={"tr": "Kullanıcı bulunamadı.", "en": "User not found."})
    return _ok({"user": {
        "id": row[0],
        "email": row[1],
        "email_verified": bool(row[2]),
        "display_name": row[3],
        "role": row[4],
        "is_active": bool(row[5]),
        "last_login_at": str(row[6]) if row[6] else None,
        "created_at": str(row[7]) if row[7] else None,
    }})


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: int, req: RoleUpdateRequest, request: Request):
    if req.role not in {"free", "pro", "ultra", "admin"}:
        raise HTTPException(400, detail={"tr": "Geçersiz rol.", "en": "Invalid role."})
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET role=%s WHERE id=%s", (req.role, user_id))
            await cur.execute(
                "INSERT INTO audit_log (user_id, action, resource, metadata) VALUES (%s, 'user_role_change', %s, JSON_OBJECT('role', %s))",
                (user_id, f"users/{user_id}", req.role),
            )
            await conn.commit()
    return _ok({"message": "Rol güncellendi."})


@router.patch("/users/{user_id}/plan")
async def update_user_plan(user_id: int, req: RoleUpdateRequest, request: Request):
    return await update_user_role(user_id, req, request)


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: int, request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_active=FALSE WHERE id=%s", (user_id,))
            await conn.commit()
    await revoke_all_user_tokens(pool, user_id)
    return _ok({"message": "Kullanıcı pasifleştirildi."})


@router.post("/users/{user_id}/unban")
async def unban_user(user_id: int, request: Request):
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_active=TRUE WHERE id=%s", (user_id,))
            await conn.commit()
    return _ok({"message": "Kullanıcı aktifleştirildi."})


@router.delete("/users/{user_id}/sessions")
async def revoke_user_sessions(user_id: int, request: Request):
    await revoke_all_user_tokens(_get_pool(request), user_id)
    return _ok({"message": "Oturumlar kapatıldı."})


@router.get("/audit-log")
async def audit_log(request: Request, user_id: int | None = None, action: str = "", limit: int = 100):
    pool = _get_pool(request)
    clauses = ["1=1"]
    params: list[object] = []
    if user_id is not None:
        clauses.append("user_id=%s")
        params.append(user_id)
    if action:
        clauses.append("action=%s")
        params.append(action)
    params.append(max(1, min(limit, 500)))
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""SELECT id, user_id, action, resource, ip_address, metadata, created_at
                    FROM audit_log
                    WHERE {' AND '.join(clauses)}
                    ORDER BY created_at DESC LIMIT %s""",
                params,
            )
            rows = await cur.fetchall()
    return _ok({"events": [
        {"id": r[0], "user_id": r[1], "action": r[2], "resource": r[3], "ip_address": r[4], "metadata": r[5], "created_at": str(r[6])}
        for r in rows
    ]})

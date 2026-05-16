"""
Ödeme Router — /api/payments/* endpoint'leri.
main.py'e:
    from backend.api.payments_router import router as payments_router
    app.include_router(payments_router, prefix="/api/payments", tags=["payments"])
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.payments.stripe_service import StripeService

_logger = logging.getLogger(__name__)
router = APIRouter()


class CheckoutRequest(BaseModel):
    plan: str            # 'pro' | 'ultra'
    billing_period: str  # 'monthly' | 'yearly'


def _ok(data: dict | None = None) -> dict:
    return {"ok": True, "data": data or {}}


def _get_pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            503,
            detail={
                "tr": "Ödeme veritabanı hazır değil.",
                "en": "Payments database is not available.",
            },
        )
    return pool


# ── Checkout ──────────────────────────────────────────────────────────────────

@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Stripe Checkout URL oluştur, kullanıcıyı oraya yönlendir."""
    user_id = int(user["sub"])
    email   = user.get("email", "")
    pool    = _get_pool(request)

    # Mevcut stripe_customer_id varsa al
    stripe_customer_id = None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT stripe_customer_id FROM user_subscriptions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                    (user_id,),
                )
                row = await cur.fetchone()
                if row and row[0]:
                    stripe_customer_id = row[0]
    except Exception:
        pass

    try:
        url = await StripeService.create_checkout_session(
            user_id=user_id,
            email=email,
            plan=req.plan,
            billing_period=req.billing_period,
            stripe_customer_id=stripe_customer_id,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, detail={"tr": str(exc), "en": str(exc)})

    return _ok({"checkout_url": url})


# ── Subscription status ──────────────────────────────────────────────────────

@router.get("/subscription")
async def get_subscription(request: Request, user: dict = Depends(get_current_user)):
    """Mevcut abonelik durumunu döndür."""
    pool = _get_pool(request)
    user_id = int(user["sub"])
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT sp.slug, sp.display_name_tr, us.billing_period, us.status,
                              us.current_period_start, us.current_period_end,
                              us.stripe_subscription_id, us.stripe_customer_id
                       FROM user_subscriptions us
                       JOIN subscription_plans sp ON sp.id = us.plan_id
                       WHERE us.user_id = %s
                       ORDER BY us.created_at DESC
                       LIMIT 1""",
                    (user_id,),
                )
                row = await cur.fetchone()
    except Exception as exc:
        raise HTTPException(500, detail={"tr": str(exc), "en": str(exc)})

    if not row:
        return _ok({"plan": user.get("role", "free"), "status": "free"})
    return _ok({
        "plan": row[0],
        "display_name": row[1],
        "billing_period": row[2],
        "status": row[3],
        "current_period_start": str(row[4]) if row[4] else None,
        "current_period_end": str(row[5]) if row[5] else None,
        "stripe_subscription_id": row[6],
        "stripe_customer_id": row[7],
    })


@router.post("/cancel")
async def cancel_subscription(request: Request, user: dict = Depends(get_current_user)):
    """Aktif Stripe aboneliğini dönem sonunda iptal et."""
    pool = _get_pool(request)
    user_id = int(user["sub"])
    stripe_subscription_id = None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT stripe_subscription_id
                       FROM user_subscriptions
                       WHERE user_id = %s AND status IN ('trialing', 'active', 'past_due')
                       ORDER BY created_at DESC LIMIT 1""",
                    (user_id,),
                )
                row = await cur.fetchone()
                if row:
                    stripe_subscription_id = row[0]
    except Exception as exc:
        raise HTTPException(500, detail={"tr": str(exc), "en": str(exc)})

    if not stripe_subscription_id:
        raise HTTPException(404, detail={"tr": "Aktif abonelik bulunamadı.", "en": "No active subscription found."})
    ok = await StripeService.cancel_subscription(stripe_subscription_id)
    if not ok:
        raise HTTPException(500, detail={"tr": "Abonelik iptal edilemedi.", "en": "Subscription could not be cancelled."})
    return _ok({"message": "Abonelik dönem sonunda iptal edilecek."})


# ── Webhook ───────────────────────────────────────────────────────────────────

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """
    Stripe webhook olaylarını işle.
    Desteklenen olaylar:
      - checkout.session.completed  → abonelik aktifleştir, rol güncelle
      - customer.subscription.updated → plan değişimi
      - customer.subscription.deleted → iptal → free'ye düşür
      - invoice.payment_failed        → past_due olarak işaretle
    """
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = StripeService.construct_webhook_event(payload, sig_header)
    except Exception as exc:
        _logger.warning("[webhook] Doğrulama hatası: %s", exc)
        raise HTTPException(400, detail="Webhook doğrulaması başarısız.")

    pool = _get_pool(request)

    # İdempotency: aynı event iki kez işlenmesin
    event_id = event["id"]
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT IGNORE INTO stripe_events (id, type) VALUES (%s, %s)",
                    (event_id, event["type"]),
                )
                if cur.rowcount == 0:
                    return {"status": "duplicate"}   # daha önce işlendi
                await conn.commit()
    except Exception as exc:
        _logger.error("[webhook] İdempotency kayıt hatası: %s", exc)

    # Olay işleme
    etype = event["type"]
    data  = event["data"]["object"]

    if etype == "checkout.session.completed":
        await _handle_checkout_completed(pool, data)

    elif etype == "customer.subscription.updated":
        await _handle_subscription_updated(pool, data)

    elif etype == "customer.subscription.deleted":
        await _handle_subscription_deleted(pool, data)

    elif etype == "invoice.payment_failed":
        await _handle_payment_failed(pool, data)

    return {"status": "ok"}


async def _handle_checkout_completed(pool, session: dict) -> None:
    """checkout.session.completed → kullanıcı rolünü güncelle."""
    user_id        = int(session.get("client_reference_id") or 0)
    plan           = (session.get("metadata") or {}).get("plan", "free")
    billing_period = (session.get("metadata") or {}).get("billing_period", "monthly")
    stripe_sub_id  = session.get("subscription")
    stripe_cust_id = session.get("customer")

    if not user_id:
        return

    # Plan slug → plan_id
    plan_id = await _get_plan_id(pool, plan)
    if not plan_id:
        return

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Abonelik kaydı oluştur/güncelle
                await cur.execute(
                    """INSERT INTO user_subscriptions
                       (user_id, plan_id, stripe_subscription_id, stripe_customer_id, billing_period, status)
                       VALUES (%s, %s, %s, %s, %s, 'active')
                       ON DUPLICATE KEY UPDATE
                         status = 'active',
                         stripe_subscription_id = %s,
                         stripe_customer_id = %s,
                         updated_at = NOW()""",
                    (user_id, plan_id, stripe_sub_id, stripe_cust_id, billing_period,
                     stripe_sub_id, stripe_cust_id),
                )
                # Kullanıcı rolünü güncelle
                await cur.execute(
                    "UPDATE users SET role = %s WHERE id = %s",
                    (plan, user_id),
                )
                await conn.commit()
        _logger.info("[webhook] Kullanıcı %s → %s planına geçirildi.", user_id, plan)
    except Exception as exc:
        _logger.error("[webhook] checkout_completed hatası: %s", exc)


async def _handle_subscription_updated(pool, sub: dict) -> None:
    """Plan değişikliği — yeni plan bilgisine göre rol güncelle."""
    stripe_sub_id = sub.get("id")
    status        = sub.get("status", "active")
    if not stripe_sub_id:
        return

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_subscriptions SET status = %s WHERE stripe_subscription_id = %s",
                    (status, stripe_sub_id),
                )
                await conn.commit()
    except Exception as exc:
        _logger.error("[webhook] subscription_updated hatası: %s", exc)


async def _handle_subscription_deleted(pool, sub: dict) -> None:
    """Abonelik iptali — kullanıcıyı free'ye düşür."""
    stripe_sub_id = sub.get("id")
    if not stripe_sub_id:
        return

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_subscriptions SET status = 'cancelled' WHERE stripe_subscription_id = %s",
                    (stripe_sub_id,),
                )
                # Kullanıcı rolünü free'ye al
                await cur.execute(
                    """UPDATE users SET role = 'free'
                       WHERE id = (
                           SELECT user_id FROM user_subscriptions
                           WHERE stripe_subscription_id = %s LIMIT 1
                       )""",
                    (stripe_sub_id,),
                )
                await conn.commit()
        _logger.info("[webhook] Abonelik iptal → kullanıcı free'ye düşürüldü. sub=%s", stripe_sub_id)
    except Exception as exc:
        _logger.error("[webhook] subscription_deleted hatası: %s", exc)


async def _handle_payment_failed(pool, invoice: dict) -> None:
    """Ödeme başarısız → past_due olarak işaretle."""
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_subscriptions SET status = 'past_due' WHERE stripe_subscription_id = %s",
                    (stripe_sub_id,),
                )
                await conn.commit()
    except Exception as exc:
        _logger.error("[webhook] payment_failed hatası: %s", exc)


async def _get_plan_id(pool, slug: str) -> int | None:
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM subscription_plans WHERE slug = %s", (slug,))
                row = await cur.fetchone()
                return row[0] if row else None
    except Exception:
        return None


# ── Faturalama Portalı ────────────────────────────────────────────────────────

@router.post("/portal")
async def billing_portal(request: Request, user: dict = Depends(get_current_user)):
    """Kullanıcıyı Stripe self-service portalına yönlendir."""
    pool    = _get_pool(request)
    user_id = int(user["sub"])

    stripe_customer_id = None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT stripe_customer_id FROM user_subscriptions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                    (user_id,),
                )
                row = await cur.fetchone()
                if row:
                    stripe_customer_id = row[0]
    except Exception:
        pass

    if not stripe_customer_id:
        raise HTTPException(404, detail={"tr": "Abonelik bulunamadı.", "en": "No subscription found."})

    try:
        url = await StripeService.get_customer_portal_url(stripe_customer_id)
    except Exception as exc:
        raise HTTPException(500, detail={"tr": str(exc), "en": str(exc)})

    return _ok({"portal_url": url})

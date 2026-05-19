"""
Billing Router — /api/billing/* endpoint'leri.

Task 3 (Bölüm 5.1 + 5.2):
  POST /api/billing/checkout   → Stripe Checkout Session oluştur
  POST /api/billing/portal     → Stripe Customer Portal URL
  POST /api/billing/webhook    → Stripe event webhook handler

STRIPE_SECRET_KEY .env'de yoksa tüm endpoint'ler 503 döndürür.
İdempotency: stripe_events SQLite tablosu ile çift işlem engellenir.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user

_logger = logging.getLogger(__name__)
router = APIRouter()

_ROOT = Path(__file__).resolve().parents[2]
_STRIPE_EVENTS_DB = _ROOT / "data" / "billing" / "stripe_events.sqlite3"

# ── Stripe availability guard ────────────────────────────────────────────────

_STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
_STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
_STRIPE_PRICE_PRO_MONTHLY = os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")
_STRIPE_PRICE_ULTRA_MONTHLY = os.environ.get("STRIPE_PRICE_ULTRA_MONTHLY", "")


def _require_stripe():
    """Stripe yapılandırılmamışsa 503 fırlat."""
    if not _STRIPE_KEY:
        raise HTTPException(
            status_code=503,
            detail={"detail": "Ödeme sistemi henüz yapılandırılmadı."},
        )


try:
    import stripe as _stripe_lib
    _STRIPE_AVAILABLE = True
    if _STRIPE_KEY:
        _stripe_lib.api_key = _STRIPE_KEY
except ImportError:
    _stripe_lib = None  # type: ignore[assignment]
    _STRIPE_AVAILABLE = False


# ── İdempotency — SQLite stripe_events ────────────────────────────────────────

def _events_db() -> sqlite3.Connection:
    _STRIPE_EVENTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_STRIPE_EVENTS_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stripe_events (
            event_id   TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            processed_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    return conn


def _is_duplicate_event(event_id: str) -> bool:
    """İdempotency kontrolü — aynı event tekrar işlenmesin."""
    with _events_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM stripe_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if row:
            return True
        conn.execute(
            "INSERT INTO stripe_events (event_id, event_type) VALUES (?, 'pending')",
            (event_id,),
        )
        conn.commit()
        return False


def _mark_event_processed(event_id: str, event_type: str) -> None:
    with _events_db() as conn:
        conn.execute(
            "UPDATE stripe_events SET event_type = ? WHERE event_id = ?",
            (event_type, event_id),
        )
        conn.commit()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str = "pro"               # 'pro' | 'ultra'
    billing_period: str = "monthly" # 'monthly' | 'yearly'


# ── Endpoints ────────────────────────────────────────────────────────────────

BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://piyasapilotu.com")


@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Stripe Checkout Session oluştur, {url} döndür."""
    _require_stripe()
    if not _STRIPE_AVAILABLE:
        raise HTTPException(503, detail="stripe paketi kurulu değil.")

    price_map = {
        "pro": _STRIPE_PRICE_PRO_MONTHLY,
        "ultra": _STRIPE_PRICE_ULTRA_MONTHLY,
    }
    price_id = price_map.get(req.plan, "")
    if not price_id:
        raise HTTPException(400, detail=f"Geçersiz plan: {req.plan}")

    user_id = int(user["sub"])
    email = user.get("email", "")

    try:
        session = _stripe_lib.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{BASE_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/pricing",
            client_reference_id=str(user_id),
            customer_email=email,
            metadata={
                "user_id": str(user_id),
                "plan": req.plan,
                "billing_period": req.billing_period,
            },
        )
        return {"url": session.url}
    except Exception as exc:
        _logger.error("[billing] Checkout hatası: %s", exc)
        raise HTTPException(500, detail=str(exc))


@router.post("/portal")
async def billing_portal(
    request: Request,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Stripe Customer Portal Session, {url} döndür."""
    _require_stripe()
    if not _STRIPE_AVAILABLE:
        raise HTTPException(503, detail="stripe paketi kurulu değil.")

    # MySQL pool varsa stripe_customer_id'yi al
    pool = getattr(request.app.state, "db_pool", None)
    stripe_customer_id = None
    if pool:
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT stripe_customer_id FROM user_subscriptions "
                        "WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                        (int(user["sub"]),),
                    )
                    row = await cur.fetchone()
                    if row and row[0]:
                        stripe_customer_id = row[0]
        except Exception:
            pass

    if not stripe_customer_id:
        raise HTTPException(404, detail="Abonelik bulunamadı.")

    try:
        session = _stripe_lib.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{BASE_URL}/settings",
        )
        return {"url": session.url}
    except Exception as exc:
        _logger.error("[billing] Portal hatası: %s", exc)
        raise HTTPException(500, detail=str(exc))


@router.post("/webhook", include_in_schema=False)
async def billing_webhook(request: Request) -> dict[str, Any]:
    """Stripe Webhook — imza doğrulaması + event işleme.

    Events:
      - checkout.session.completed  → user.plan güncelle
      - customer.subscription.deleted → free'ye düşür
      - invoice.payment_failed → uyarı maili gönder
    """
    _require_stripe()
    if not _STRIPE_AVAILABLE:
        raise HTTPException(503, detail="stripe paketi kurulu değil.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = _stripe_lib.Webhook.construct_event(
            payload, sig_header, _STRIPE_WEBHOOK_SECRET,
        )
    except Exception as exc:
        _logger.warning("[billing-webhook] İmza doğrulaması başarısız: %s", exc)
        raise HTTPException(400, detail="Webhook doğrulaması başarısız.")

    event_id = event["id"]
    event_type = event["type"]

    # İdempotency kontrolü
    if _is_duplicate_event(event_id):
        return {"status": "duplicate", "event_id": event_id}

    data_obj = event["data"]["object"]
    pool = getattr(request.app.state, "db_pool", None)

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout(pool, data_obj)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(pool, data_obj)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(pool, data_obj)
        else:
            _logger.info("[billing-webhook] İşlenmeyen event: %s", event_type)
    except Exception as exc:
        _logger.error("[billing-webhook] Event işleme hatası: %s", exc)

    _mark_event_processed(event_id, event_type)
    return {"status": "ok", "event_id": event_id}


# ── Event Handlers ───────────────────────────────────────────────────────────

async def _handle_checkout(pool: Any, session: dict) -> None:
    """checkout.session.completed → kullanıcı planını güncelle."""
    user_id = int(session.get("client_reference_id") or 0)
    plan = (session.get("metadata") or {}).get("plan", "pro")
    if not user_id or not pool:
        return
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET role = %s WHERE id = %s",
                    (plan, user_id),
                )
                await conn.commit()
        _logger.info("[billing] Kullanıcı %s → %s planına geçti.", user_id, plan)
    except Exception as exc:
        _logger.error("[billing] Checkout plan güncelleme hatası: %s", exc)


async def _handle_subscription_deleted(pool: Any, sub: dict) -> None:
    """customer.subscription.deleted → free'ye düşür."""
    stripe_sub_id = sub.get("id")
    if not stripe_sub_id or not pool:
        return
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """UPDATE users SET role = 'free'
                       WHERE id = (
                           SELECT user_id FROM user_subscriptions
                           WHERE stripe_subscription_id = %s LIMIT 1
                       )""",
                    (stripe_sub_id,),
                )
                await conn.commit()
        _logger.info("[billing] Abonelik iptal → free. sub=%s", stripe_sub_id)
    except Exception as exc:
        _logger.error("[billing] Subscription deleted hatası: %s", exc)


async def _handle_payment_failed(pool: Any, invoice: dict) -> None:
    """invoice.payment_failed → uyarı e-postası gönder."""
    customer_email = invoice.get("customer_email", "")
    if customer_email:
        try:
            from backend.auth.email_sender import send_payment_failed_email
            send_payment_failed_email(customer_email)
        except Exception as exc:
            _logger.warning("[billing] Payment failed email gönderilemedi: %s", exc)

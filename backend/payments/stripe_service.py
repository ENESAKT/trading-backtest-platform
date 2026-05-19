"""
Stripe Ödeme Servisi.
stripe kütüphanesi kurulu değilse import'lar gracefully başarısız olur.
"""

from __future__ import annotations
import logging
import os
from typing import Any

_logger = logging.getLogger(__name__)

try:
    import stripe  # type: ignore
    _STRIPE_AVAILABLE = True
except ImportError:
    stripe = None  # type: ignore[assignment]
    _STRIPE_AVAILABLE = False
    _logger.warning("[payments] stripe paketi kurulu değil. pip install stripe --break-system-packages")


STRIPE_SECRET_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID    = os.environ.get("STRIPE_PRO_PRICE_ID", "")
STRIPE_PRO_YEARLY_PRICE_ID = os.environ.get("STRIPE_PRO_YEARLY_PRICE_ID", "")
STRIPE_ULTRA_PRICE_ID  = os.environ.get("STRIPE_ULTRA_PRICE_ID", "")
STRIPE_ULTRA_YEARLY_PRICE_ID = os.environ.get("STRIPE_ULTRA_YEARLY_PRICE_ID", "")
BASE_URL               = os.environ.get("PUBLIC_BASE_URL", "https://piyasapilot.com")

if _STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class StripeService:

    @staticmethod
    def _require_stripe() -> None:
        if not _STRIPE_AVAILABLE:
            raise RuntimeError("stripe paketi kurulu değil.")
        if not STRIPE_SECRET_KEY:
            raise RuntimeError("STRIPE_SECRET_KEY .env'de tanımlı değil.")

    # ── Checkout ─────────────────────────────────────────────────────────

    @staticmethod
    async def create_checkout_session(
        user_id: int,
        email: str,
        plan: str,            # 'pro' | 'ultra'
        billing_period: str,  # 'monthly' | 'yearly'
        stripe_customer_id: str | None = None,
    ) -> str:
        """Stripe Checkout URL döndür."""
        StripeService._require_stripe()

        price_map = {
            ("pro",   "monthly"): STRIPE_PRO_PRICE_ID,
            ("pro",   "yearly"):  STRIPE_PRO_YEARLY_PRICE_ID,
            ("ultra", "monthly"): STRIPE_ULTRA_PRICE_ID,
            ("ultra", "yearly"):  STRIPE_ULTRA_YEARLY_PRICE_ID,
        }
        price_id = price_map.get((plan, billing_period))
        if not price_id:
            raise ValueError(f"Geçersiz plan/dönem: {plan}/{billing_period}")

        kwargs: dict[str, Any] = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": f"{BASE_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url":  f"{BASE_URL}/pricing",
            "client_reference_id": str(user_id),
            "customer_email": email,
            "metadata": {
                "user_id":        str(user_id),
                "plan":           plan,
                "billing_period": billing_period,
            },
        }
        if stripe_customer_id:
            kwargs["customer"] = stripe_customer_id
            del kwargs["customer_email"]

        session = stripe.checkout.Session.create(**kwargs)
        return session.url

    @staticmethod
    async def cancel_subscription(stripe_subscription_id: str) -> bool:
        """Aboneliği dönem sonunda iptal et."""
        StripeService._require_stripe()
        try:
            stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True,
            )
            return True
        except stripe.error.StripeError as exc:
            _logger.error("[payments] İptal hatası: %s", exc)
            return False

    @staticmethod
    async def get_customer_portal_url(stripe_customer_id: str) -> str:
        """Müşteri self-service portalına URL döndür."""
        StripeService._require_stripe()
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{BASE_URL}/settings",
        )
        return session.url

    # ── Webhook ──────────────────────────────────────────────────────────

    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> Any:
        """Stripe webhook payload'ını doğrula ve event döndür."""
        StripeService._require_stripe()
        return stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)

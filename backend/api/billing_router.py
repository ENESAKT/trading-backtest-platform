"""
KULLANILMIYOR — Bu dosya artık aktif değil.

payments_router.py, tek yetkili Stripe handler'dır (/api/payments/*).
Bu router main.py'den kaldırıldı; burada yalnızca tarihsel referans olarak saklanmaktadır.

Stripe env değişkenleri:
  STRIPE_PRO_PRICE_ID, STRIPE_ULTRA_PRICE_ID (billing_router eski adı: STRIPE_PRICE_PRO_MONTHLY / STRIPE_PRICE_ULTRA_MONTHLY)

Webhook URL: https://piyasapilot.com/api/payments/webhook
"""

raise ImportError(
    "billing_router kaldırıldı. payments_router.py'yi kullanın (/api/payments/*)."
)

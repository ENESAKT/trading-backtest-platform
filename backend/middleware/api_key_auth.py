"""Opsiyonel X-API-Key header tabanlı kimlik doğrulama middleware.

.env'de ``API_KEY`` tanımlıysa tüm ``/api/*`` ve ``/metrics`` istekleri
bu header'ı zorunlu kılar. Tanımlı değilse middleware şeffaf geçer (lokal mod).

Kurallar:
  * ``/api/health`` ve WebSocket upgrade istekleri doğrulama dışıdır.
  * Geçersiz veya eksik key → HTTP 401.
  * Key değeri loglanmaz.
"""

from __future__ import annotations

import hmac
import os

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Opsiyonel API key doğrulama katmanı."""

    # Key doğrulamasından her zaman muaf yollar
    _ALWAYS_EXEMPT = frozenset({"/api/health"})
    # Sadece geliştirme ortamında muaf (production'da kapalı)
    _DEV_ONLY_EXEMPT = frozenset({"/docs", "/openapi.json", "/redoc"})

    @property
    def EXEMPT_PATHS(self) -> frozenset[str]:
        is_prod = os.environ.get("APP_ENV", "development") == "production"
        if is_prod:
            return self._ALWAYS_EXEMPT
        return self._ALWAYS_EXEMPT | self._DEV_ONLY_EXEMPT

    def _get_api_key(self) -> str:
        """API key'i her istekte ortam değişkeninden oku (test izolasyonu için)."""
        import os
        return os.environ.get("API_KEY", "")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        api_key = self._get_api_key()
        if not api_key:
            # API_KEY tanımlı değil → middleware devre dışı (lokal geliştirme)
            return await call_next(request)

        path = request.url.path

        # Muaf yollar
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # WebSocket istekleri ayrı doğrulanır (upgrade header)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Sadece /api/* ve /metrics yollarını kontrol et
        if not (path.startswith("/api/") or path == "/metrics"):
            return await call_next(request)

        # Header kontrolü — sabit-zamanlı karşılaştırma (timing attack'e karşı)
        provided_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(provided_key, api_key):
            return JSONResponse(
                {"detail": "Geçersiz veya eksik API anahtarı."},
                status_code=401,
            )

        return await call_next(request)

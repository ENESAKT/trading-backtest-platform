"""VİOP veri sağlayıcı iskeleti.

Lisanslı/resmi veri kaynağı yapılandırılmadığı sürece veri üretmez.
"""

from __future__ import annotations

from quant_engine.data.market_data import (
    MarketDataHealth,
    MarketDataProviderType,
    MarketDataResult,
    MarketDataStatus,
    utc_iso,
)
from quant_engine.data.providers.http_ohlcv import (
    configured_header,
    configured_template,
    fetch_http_ohlcv,
)


class ViopMarketDataProvider:
    name = "viop_not_configured"
    source = "Borsa İstanbul VİOP lisanslı/veri sağlayıcı bağlantısı yok"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.last_success_at: str | None = None
        self.last_error: str | None = None

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> MarketDataResult:
        clean = symbol.strip().upper()
        template = configured_template("VIOP_HTTP_URL_TEMPLATE")
        timestamp = utc_iso()
        if template:
            try:
                bars = fetch_http_ohlcv(
                    template,
                    clean,
                    timeframe,
                    limit,
                    self.timeout,
                    configured_header("VIOP_HTTP_AUTH_HEADER"),
                )
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"{type(exc).__name__}: {exc}"
                bars = []
            if bars:
                self.last_success_at = timestamp
                self.last_error = None
                return MarketDataResult(
                    symbol=clean,
                    market="viop",
                    timeframe=timeframe,
                    data=bars,
                    source="Configured VİOP HTTP feed",
                    is_real=True,
                    status=MarketDataStatus.OK,
                    timestamp=timestamp,
                    provider_name="viop_http",
                    display_name=clean,
                )

            self.last_error = self.last_error or "VİOP HTTP feed veri döndürmedi."
            return MarketDataResult(
                symbol=clean,
                market="viop",
                timeframe=timeframe,
                data=[],
                source="Configured VİOP HTTP feed",
                is_real=False,
                status=MarketDataStatus.NO_DATA,
                timestamp=timestamp,
                error=self.last_error,
                provider_name="viop_http",
                display_name=clean,
            )

        return MarketDataResult(
            symbol=clean,
            market="viop",
            timeframe=timeframe,
            data=[],
            source=self.source,
            is_real=False,
            status=MarketDataStatus.NOT_CONFIGURED,
            timestamp=timestamp,
            error="VİOP veri sağlayıcısı henüz yapılandırılmadı.",
            provider_name=self.name,
            display_name=clean,
        )

    def health(self) -> MarketDataHealth:
        configured = bool(configured_template("VIOP_HTTP_URL_TEMPLATE"))
        last_error = (
            self.last_error if configured else "VİOP veri sağlayıcısı henüz yapılandırılmadı."
        )
        return MarketDataHealth(
            provider_name="viop_http" if configured else self.name,
            provider_type=MarketDataProviderType.VIOP,
            active=configured,
            configured=configured,
            is_real=configured,
            supported_markets=["viop"],
            last_success_at=self.last_success_at,
            last_error=last_error,
            source="Configured VİOP HTTP feed" if configured else self.source,
        )

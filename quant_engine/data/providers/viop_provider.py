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


class ViopMarketDataProvider:
    name = "viop_not_configured"
    source = "Borsa İstanbul VİOP lisanslı/veri sağlayıcı bağlantısı yok"

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> MarketDataResult:
        del limit
        return MarketDataResult(
            symbol=symbol.strip().upper(),
            market="viop",
            timeframe=timeframe,
            data=[],
            source=self.source,
            is_real=False,
            status=MarketDataStatus.NOT_CONFIGURED,
            timestamp=utc_iso(),
            error="VİOP veri sağlayıcısı henüz yapılandırılmadı.",
            provider_name=self.name,
            display_name=symbol.strip().upper(),
        )

    def health(self) -> MarketDataHealth:
        return MarketDataHealth(
            provider_name=self.name,
            provider_type=MarketDataProviderType.VIOP,
            active=False,
            configured=False,
            supported_markets=["viop"],
            last_success_at=None,
            last_error="VİOP veri sağlayıcısı henüz yapılandırılmadı.",
            source=self.source,
        )

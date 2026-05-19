"""Sprint 10 ortak piyasa veri modelleri.

Bu katman yalnızca okuma amaçlıdır. Veri sağlayıcılar gerçek veri yoksa sahte
bar üretmez; durum ve hata bilgisiyle üst katmana bildirir.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class MarketDataStatus(str, Enum):
    OK = "ok"
    NO_DATA = "no_data"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"
    INVALID = "invalid"
    STALE = "stale"


class MarketDataProviderType(str, Enum):
    BIST = "bist"
    VIOP = "viop"
    CRYPTO = "crypto"
    CACHE = "cache"


def utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


@dataclass
class MarketDataResult:
    symbol: str
    market: str
    timeframe: str
    data: list[dict[str, Any]]
    source: str
    is_real: bool
    status: MarketDataStatus
    timestamp: str = field(default_factory=utc_iso)
    error: str = ""
    provider_name: str = ""
    display_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload

    def to_legacy_payload(self) -> dict[str, Any]:
        """Mevcut `/api/v2/candles` sözleşmesine uyumlu payload üret."""
        message = ""
        if self.status == MarketDataStatus.NO_DATA:
            message = "Veri bulunamadı."
        elif self.status == MarketDataStatus.NOT_CONFIGURED:
            message = self.error or "Veri sağlayıcısı yapılandırılmadı."
        elif self.status in {MarketDataStatus.ERROR, MarketDataStatus.INVALID}:
            message = self.error or "Veri sağlayıcı hatası."

        quote = None
        if self.data:
            quote = {
                "last": self.data[-1]["close"],
                "timestamp": self.timestamp,
            }

        return {
            "symbol": self.symbol,
            "display_name": self.display_name or self.symbol,
            "market": self.market,
            "interval": self.timeframe,
            "status": self.status.value,
            "message": message,
            "bars": self.data,
            "quote": quote,
            "metadata": {
                "source": self.source,
                "is_real": self.is_real,
                "status": self.status.value,
                "provider_name": self.provider_name,
                "market": self.market,
                "fetched_at": self.timestamp,
                "error": self.error,
                "read_only": True,
            },
        }


@dataclass
class MarketDataHealth:
    provider_name: str
    provider_type: MarketDataProviderType
    active: bool
    configured: bool
    is_real: bool
    supported_markets: list[str]
    last_success_at: str | None = None
    last_error: str | None = None
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["provider_type"] = self.provider_type.value
        return payload

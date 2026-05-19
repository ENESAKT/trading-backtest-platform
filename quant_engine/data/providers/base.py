"""
Quant Engine — Provider Temel Sınıfı

MarketDataProvider protocol'ünü implemente eden tüm provider'lar
için ortak mantığı barındırır.

Kullanım:
    from quant_engine.data.providers.base import BaseProvider
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from loguru import logger

from quant_engine.core.protocols import (
    BarRequest,
    FetchResult,
    ProviderCapabilities,
)


class BaseProvider(ABC):
    """
    Tüm veri sağlayıcılar için temel sınıf.

    Ortak özellikler:
    - Retry mekanizması
    - Loglama
    - Health check
    """

    def __init__(
        self,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.timeout = timeout

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Provider yeteneklerini döndür."""
        ...

    @abstractmethod
    def _fetch_bars_impl(
        self, request: BarRequest
    ) -> FetchResult:
        """Alt sınıfın implemente edeceği gerçek fetch."""
        ...

    def fetch_bars(self, request: BarRequest) -> FetchResult:
        """
        Retry mantığı ile bar verisi çek.

        Alt sınıflar _fetch_bars_impl() yazar, bu metod retry sarar.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.retry_count + 1):
            try:
                result = self._fetch_bars_impl(request)
                if result.success:
                    return result
                # Başarısız ama exception yok — tekrar deneme
                if attempt < self.retry_count:
                    logger.warning(
                        f"⚠️ {request.symbol}: Deneme {attempt} "
                        f"başarısız ({result.errors}), "
                        f"tekrar deneniyor..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    return result
            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"⚠️ {request.symbol}: Deneme {attempt} "
                        f"hata ({e}), {self.retry_delay}s "
                        f"bekleniyor..."
                    )
                    time.sleep(self.retry_delay)

        # Tüm denemeler başarısız
        import pandas as pd

        return FetchResult(
            symbol=request.symbol,
            data=pd.DataFrame(),
            source=self.capabilities().name,
            errors=[
                f"Tüm denemeler başarısız: {last_error}"
            ],
        )

    def health_check(self) -> bool:
        """Varsayılan health check — override edilebilir."""
        return True

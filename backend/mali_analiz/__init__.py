"""Mali analiz servis çekirdeği.

Bu paket yalnızca veri modeli, cache ve provider-bağımsız servis katmanını içerir.
FastAPI endpoint bağlantısı ayrı iş olarak bırakılmıştır.
"""

from backend.mali_analiz.cache import FinancialAnalysisCache, FinancialCacheEntry
from backend.mali_analiz.models import FinancialAnalysisResponse, SourceStatus
from backend.mali_analiz.service import (
    FinancialAnalysisProvider,
    FinancialAnalysisService,
    FinancialProviderResult,
    MockFinancialAnalysisProvider,
)

__all__ = [
    "FinancialAnalysisCache",
    "FinancialAnalysisProvider",
    "FinancialAnalysisResponse",
    "FinancialAnalysisService",
    "FinancialCacheEntry",
    "FinancialProviderResult",
    "MockFinancialAnalysisProvider",
    "SourceStatus",
]

"""Mali analiz servis çekirdeği.

Bu paket yalnızca veri modeli, cache ve provider-bağımsız servis katmanını içerir.
FastAPI endpoint bağlantısı ayrı iş olarak bırakılmıştır.
"""

from backend.mali_analiz.cache import FinancialAnalysisCache, FinancialCacheEntry
from backend.mali_analiz.models import FinancialAnalysisResponse, SourceStatus
from backend.mali_analiz.kap_provider import KapFinancialAnalysisProvider
from backend.mali_analiz.repository import FinancialStatementRepository
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
    "FinancialStatementRepository",
    "KapFinancialAnalysisProvider",
    "MockFinancialAnalysisProvider",
    "SourceStatus",
]

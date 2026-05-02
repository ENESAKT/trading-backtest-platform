"""Mali analiz provider-bağımsız servis katmanı."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

from backend.mali_analiz.cache import DEFAULT_TTL, FinancialAnalysisCache
from backend.mali_analiz.models import FinancialAnalysisResponse, SourceStatus


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol boş olamaz")
    return normalized


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FinancialProviderResult:
    payload: FinancialAnalysisResponse
    source: str
    status: str = "ok"
    fetched_at: datetime | None = None


class FinancialAnalysisProvider(Protocol):
    """Borsa/MCP/dış kaynak entegrasyonları için minimal provider arayüzü."""

    def fetch(self, symbol: str) -> FinancialProviderResult:
        """Sembol için mali analiz payload'ı döndürür."""


class MockFinancialAnalysisProvider:
    """Dış kaynak hazır değilken deterministic boş payload üreten provider."""

    source = "mock"

    def fetch(self, symbol: str) -> FinancialProviderResult:
        normalized = _normalize_symbol(symbol)
        payload = FinancialAnalysisResponse(
            symbol=normalized,
            company_name=None,
            periods=[],
            balance_sheet={},
            income_statement={},
            cash_flow={},
            ratios={},
            warnings=["Mali analiz için mock provider kullanıldı."],
        )
        return FinancialProviderResult(payload=payload, source=self.source, status="mock")


class FinancialAnalysisService:
    """Cache-first mali analiz servis çekirdeği."""

    def __init__(
        self,
        *,
        cache: FinancialAnalysisCache,
        provider: FinancialAnalysisProvider | None = None,
        ttl: timedelta = DEFAULT_TTL,
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.cache = cache
        self.provider = provider or MockFinancialAnalysisProvider()
        self.ttl = ttl
        self._now_provider = now_provider or _utc_now

    def get_analysis(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> FinancialAnalysisResponse:
        normalized = _normalize_symbol(symbol)
        now = self._now_provider().astimezone(timezone.utc)
        cached = self.cache.get(normalized)

        if (
            cached is not None
            and not force_refresh
            and cached.is_fresh(ttl=self.ttl, now=now)
        ):
            return cached.to_response(cache_hit=True, stale=False)

        try:
            result = self.provider.fetch(normalized)
        except Exception as exc:
            error = str(exc) or exc.__class__.__name__
            if cached is not None:
                warning = f"Provider hatası nedeniyle son cache döndü: {error}"
                fallback = cached.to_response(
                    cache_hit=True,
                    stale=True,
                    error=error,
                )
                return fallback.with_warning(warning)

            status = SourceStatus(
                source="none",
                status="error",
                fetched_at=None,
                cache_hit=False,
                stale=False,
                error=error,
            )
            return FinancialAnalysisResponse.empty(
                normalized,
                warning=f"Provider hatası ve kullanılabilir cache yok: {error}",
                source_status=status,
            )

        fetched_at = (result.fetched_at or now).astimezone(timezone.utc)
        payload = result.payload.model_copy(update={"symbol": normalized})
        entry = self.cache.upsert(
            normalized,
            payload,
            source=result.source,
            status=result.status,
            fetched_at=fetched_at,
        )
        return entry.to_response(cache_hit=False, stale=False)

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.mali_analiz.cache import FinancialAnalysisCache
from backend.mali_analiz.models import FinancialAnalysisResponse
from backend.mali_analiz.service import (
    FinancialAnalysisService,
    FinancialProviderResult,
    MockFinancialAnalysisProvider,
    _normalize_symbol,
)


def _dt(hour: int) -> datetime:
    return datetime(2026, 5, 2, hour, tzinfo=timezone.utc)


def _payload(symbol: str, company_name: str = "Test A.S.") -> FinancialAnalysisResponse:
    return FinancialAnalysisResponse(
        symbol=symbol,
        company_name=company_name,
        periods=["2025-Q4"],
        balance_sheet={"assets": {"2025-Q4": 1000}},
        income_statement={"revenue": {"2025-Q4": 250}},
        cash_flow={"operating_cash_flow": {"2025-Q4": 80}},
        financial_statements=[],
        ratios=[{"name": "current_ratio", "value": 1.6, "format": "num"}],
    )


@dataclass
class StaticProvider:
    payload: FinancialAnalysisResponse
    source: str = "unit"
    status: str = "ok"
    fetched_at: datetime | None = None
    calls: int = 0

    def fetch(self, symbol: str) -> FinancialProviderResult:
        self.calls += 1
        return FinancialProviderResult(
            payload=self.payload.model_copy(update={"symbol": symbol}),
            source=self.source,
            status=self.status,
            fetched_at=self.fetched_at,
        )


class FailingProvider:
    def __init__(self, message: str = "provider down"):
        self.message = message

    def fetch(self, symbol: str) -> FinancialProviderResult:
        raise RuntimeError(self.message)


def test_cache_ttl_returns_fresh_cache_without_provider_call(tmp_path):
    cache = FinancialAnalysisCache(tmp_path / "mali.sqlite3")
    cache.upsert(
        "THYAO",
        _payload("THYAO"),
        source="unit-cache",
        status="ok",
        fetched_at=_dt(8),
    )
    provider = StaticProvider(_payload("THYAO", "Provider A.S."))
    service = FinancialAnalysisService(
        cache=cache,
        provider=provider,
        now_provider=lambda: _dt(20),
    )

    response = service.get_analysis("thyao")

    assert provider.calls == 0
    assert response.company_name == "Test A.S."
    assert response.source_status.cache_hit is True
    assert response.source_status.stale is False
    assert response.source_status.source == "unit-cache"


def test_expired_cache_refreshes_from_provider_and_updates_cache(tmp_path):
    cache = FinancialAnalysisCache(tmp_path / "mali.sqlite3")
    cache.upsert(
        "THYAO",
        _payload("THYAO", "Old A.S."),
        source="old",
        status="ok",
        fetched_at=_dt(1),
    )
    provider = StaticProvider(
        _payload("THYAO", "Fresh A.S."),
        source="provider",
        fetched_at=_dt(23),
    )
    service = FinancialAnalysisService(
        cache=cache,
        provider=provider,
        now_provider=lambda: _dt(23) + timedelta(days=1),
    )

    response = service.get_analysis("THYAO")

    assert provider.calls == 1
    assert response.company_name == "Fresh A.S."
    assert response.source_status.cache_hit is False
    assert response.source_status.source == "provider"
    cached = cache.get("THYAO")
    assert cached is not None
    assert cached.payload.company_name == "Fresh A.S."


def test_provider_failure_returns_last_cache_as_stale_fallback(tmp_path):
    cache = FinancialAnalysisCache(tmp_path / "mali.sqlite3")
    cache.upsert(
        "ASELS",
        _payload("ASELS"),
        source="old-provider",
        status="ok",
        fetched_at=_dt(1),
    )
    service = FinancialAnalysisService(
        cache=cache,
        provider=FailingProvider("network unavailable"),
        now_provider=lambda: _dt(23) + timedelta(days=2),
    )

    response = service.get_analysis("ASELS")

    assert response.company_name == "Test A.S."
    assert response.source_status.cache_hit is True
    assert response.source_status.stale is True
    assert response.source_status.error == "network unavailable"
    assert any("son cache döndü" in w for w in response.warnings)


def test_provider_failure_without_cache_returns_controlled_warning_response(tmp_path):
    cache = FinancialAnalysisCache(tmp_path / "mali.sqlite3")
    service = FinancialAnalysisService(
        cache=cache,
        provider=FailingProvider("timeout"),
        now_provider=lambda: _dt(10),
    )

    response = service.get_analysis("KCHOL")

    assert response.symbol == "KCHOL"
    assert response.company_name is None
    assert response.periods == []
    assert response.balance_sheet == {}
    assert response.income_statement == {}
    assert response.cash_flow == {}
    assert response.ratios == []
    assert response.source_status.status == "provider_error"
    assert response.source_status.cache_hit is False
    assert response.source_status.error == "timeout"
    assert any("Provider hatası" in w for w in response.warnings)


def test_response_model_is_json_serializable(tmp_path):
    cache = FinancialAnalysisCache(tmp_path / "mali.sqlite3")
    provider = StaticProvider(_payload("SISE"), source="provider", fetched_at=_dt(9))
    service = FinancialAnalysisService(
        cache=cache,
        provider=provider,
        now_provider=lambda: _dt(9),
    )

    response = service.get_analysis("sise")
    encoded = response.model_dump_json()
    decoded = json.loads(encoded)

    assert decoded["symbol"] == "SISE"
    assert decoded["source_status"]["fetched_at"] == "2026-05-02T09:00:00Z"
    assert set(decoded) == {
        "symbol",
        "company_name",
        "periods",
        "balance_sheet",
        "income_statement",
        "cash_flow",
        "financial_statements",
        "ratios",
        "source_status",
        "warnings",
    }


def test_normalize_symbol_trims_uppercases_and_removes_bist_suffix():
    assert _normalize_symbol(" thyao.is ") == "THYAO"


def test_normalize_symbol_rejects_empty_symbol():
    try:
        _normalize_symbol(" .is ")
    except ValueError as exc:
        assert "symbol boş olamaz" in str(exc)
    else:
        raise AssertionError("empty symbol should raise ValueError")


def test_mock_provider_returns_metadata_only_without_fake_financials():
    provider = MockFinancialAnalysisProvider()

    result = provider.fetch(" THYAO.IS ")
    payload = result.payload

    assert isinstance(payload, FinancialAnalysisResponse)
    assert payload.symbol == "THYAO"
    assert payload.company_name
    assert payload.periods == []
    assert payload.financial_statements == []
    assert payload.ratios == []
    assert result.status == "metadata_only"
    assert "Şirket adı yok" not in payload.warnings
    assert "Finansal tablo verisi henüz bağlı değil." in payload.warnings

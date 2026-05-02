"""Mali analiz API entegrasyon testleri."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.mali_analiz.cache import FinancialAnalysisCache
from backend.mali_analiz.models import FinancialAnalysisResponse
from backend.mali_analiz.service import FinancialAnalysisService, FinancialProviderResult
from backend.workers import WorkerSupervisor


class FakeFinancialProvider:
    def __init__(self):
        self.should_fail = False
        self.calls = 0

    def fetch(self, symbol: str) -> FinancialProviderResult:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("Provider error")

        payload = FinancialAnalysisResponse(
            symbol=symbol.upper(),
            company_name=f"{symbol} Corp",
            periods=["2023/12"],
            balance_sheet={"donen_varliklar": 1000},
            income_statement={"net_kar": 100},
            cash_flow={},
            ratios=[],
            warnings=[],
        )
        return FinancialProviderResult(payload=payload, source="fake")


def _build_client(tmp_path) -> tuple[TestClient, FakeFinancialProvider, FinancialAnalysisCache]:
    ma_cache = FinancialAnalysisCache(db_path=tmp_path / "mali_analiz.sqlite3")
    fake_provider = FakeFinancialProvider()
    service = FinancialAnalysisService(cache=ma_cache, provider=fake_provider)

    app = create_app(
        mali_analiz_service=service,
        supervisor=WorkerSupervisor([]),
    )
    return TestClient(app), fake_provider, ma_cache


def test_mali_analiz_endpoint_success(tmp_path):
    client, provider, _ = _build_client(tmp_path)

    resp = client.get("/api/mali-analiz/THYAO")
    assert resp.status_code == 200
    body = resp.json()

    assert body["symbol"] == "THYAO"
    assert body["company_name"] == "THYAO Corp"
    assert body["source_status"]["cache_hit"] is False
    assert provider.calls == 1


def test_mali_analiz_endpoint_cache_hit(tmp_path):
    client, provider, _ = _build_client(tmp_path)

    # First call - cache miss
    client.get("/api/mali-analiz/THYAO")
    assert provider.calls == 1

    # Second call - cache hit
    resp = client.get("/api/mali-analiz/THYAO")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_status"]["cache_hit"] is True
    assert provider.calls == 1  # No new provider call


def test_mali_analiz_endpoint_force_refresh(tmp_path):
    client, provider, _ = _build_client(tmp_path)

    client.get("/api/mali-analiz/THYAO")
    resp = client.get("/api/mali-analiz/THYAO", params={"force_refresh": True})

    assert resp.status_code == 200
    body = resp.json()
    assert body["source_status"]["cache_hit"] is False
    assert provider.calls == 2


def test_mali_analiz_endpoint_provider_error_with_fallback(tmp_path):
    client, provider, _ = _build_client(tmp_path)

    # 1) Fill cache
    client.get("/api/mali-analiz/THYAO")

    # 2) Provider fails, but we have cache
    provider.should_fail = True
    resp = client.get("/api/mali-analiz/THYAO", params={"force_refresh": True})

    assert resp.status_code == 200
    body = resp.json()
    assert body["source_status"]["stale"] is True
    assert any("Provider hatası" in w for w in body["warnings"])


def test_mali_analiz_endpoint_invalid_symbol(tmp_path):
    client, _, _ = _build_client(tmp_path)
    resp = client.get("/api/mali-analiz/ ")
    assert resp.status_code == 400
    assert "symbol boş olamaz" in resp.json()["detail"]

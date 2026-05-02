"""Mali analiz response modelleri."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceStatus(BaseModel):
    """Verinin hangi kaynaktan ve hangi güvenilirlik durumuyla geldiğini anlatır."""

    model_config = ConfigDict(extra="forbid")

    source: str = "none"
    status: str = "unknown"
    fetched_at: datetime | None = None
    cache_hit: bool = False
    stale: bool = False
    error: str | None = None


class FinancialAnalysisResponse(BaseModel):
    """Mali analiz sekmesinin ihtiyaç duyacağı temel, JSON-serializable response."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    company_name: str | None = None
    periods: list[str] = Field(default_factory=list)
    balance_sheet: dict[str, Any] = Field(default_factory=dict)
    income_statement: dict[str, Any] = Field(default_factory=dict)
    cash_flow: dict[str, Any] = Field(default_factory=dict)
    ratios: dict[str, Any] = Field(default_factory=dict)
    source_status: SourceStatus = Field(default_factory=SourceStatus)
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def empty(
        cls,
        symbol: str,
        *,
        warning: str,
        source_status: SourceStatus | None = None,
    ) -> "FinancialAnalysisResponse":
        return cls(
            symbol=symbol,
            source_status=source_status or SourceStatus(status="error"),
            warnings=[warning],
        )

    def with_source_status(self, source_status: SourceStatus) -> "FinancialAnalysisResponse":
        return self.model_copy(update={"source_status": source_status})

    def with_warning(self, warning: str) -> "FinancialAnalysisResponse":
        warnings = [*self.warnings, warning]
        return self.model_copy(update={"warnings": warnings})

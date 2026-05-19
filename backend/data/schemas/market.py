"""Piyasa verisi şemaları — DataTruth kontratı dahil.

DataTruth: her veri yanıtına eklenen kalite ve soy ağacı (lineage) bilgisi.
Bu yapı Bölüm 18.2 gereksinimlerine karşılık gelir.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ─── Temel Bar Modeli ────────────────────────────────────────────────────────

class MarketBar(BaseModel):
    market:           str
    symbol:           str
    instrument_type:  str
    timeframe:        str
    ts:               datetime
    open:             float
    high:             float
    low:              float
    close:            float
    volume:           float
    source:           str  = "provider"
    source_timeframe: str  = ""
    is_derived:       bool = False
    quality_status:   str  = "ok"
    ingest_job_id:    Optional[str]      = None
    ingested_at:      Optional[datetime] = None


# ─── DataTruth Kontratı (Bölüm 18.2) ────────────────────────────────────────

SourceType = Literal[
    "licensed",
    "exchange_public",
    "broker",
    "cache",
    "imported_csv",
    "sample",
    "unknown",
]

QualityStatus = Literal["ok", "warning", "blocked", "unknown"]


class DataTruth(BaseModel):
    """Veri kalitesi ve soy ağacı — her veri yanıtına eklenir."""

    # Kimlik
    symbol:    str
    market:    str
    timeframe: str

    # Kaynak bilgisi
    provider:    str          = "unknown"
    source_type: SourceType   = "unknown"

    # Gerçeklik durumu
    is_real:      bool = False
    is_live:      bool = False
    is_delayed:   bool = False
    delay_minutes: int = 0

    # Zaman bilgisi
    fetched_at:       Optional[datetime] = None
    first_bar_ts:     Optional[datetime] = None
    last_bar_ts:      Optional[datetime] = None
    last_provider_ts: Optional[datetime] = None
    staleness_seconds: int = 0

    # Kalite metrikleri
    quality_status:  QualityStatus = "unknown"
    coverage_pct:    float         = Field(default=0.0, ge=0.0, le=100.0)
    gap_count:       int           = 0
    duplicate_count: int           = 0
    outlier_count:   int           = 0

    # Düzeltme bilgisi
    adjusted_for_splits:    bool = False
    adjusted_for_dividends: bool = False

    # Türetme bilgisi
    is_derived:        bool = False
    source_timeframe:  str  = ""
    derivation_method: str  = ""

    # Lisans / uyarı
    license_note: str        = ""
    warnings:     List[str]  = Field(default_factory=list)

    @classmethod
    def unknown(cls, symbol: str, market: str, timeframe: str) -> "DataTruth":
        """Bilinmeyen / metadata eksik durum — her zaman uyarı üretir."""
        return cls(
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            quality_status="unknown",
            warnings=["Veri metadata bilgisi alınamadı. Sonuçlar doğrulanmamıştır."],
        )

    @classmethod
    def from_bar_metadata(
        cls,
        symbol: str,
        market: str,
        timeframe: str,
        is_real: bool,
        source: str,
        is_derived: bool = False,
        source_timeframe: str = "",
        coverage_pct: float = 0.0,
        fetched_at: Optional[datetime] = None,
    ) -> "DataTruth":
        """Bar yanıtı metadata'sından DataTruth oluştur."""
        quality: QualityStatus = "ok" if is_real else "warning"
        source_type: SourceType = "cache" if source == "cache" else (
            "licensed" if is_real else "exchange_public"
        )
        warnings: list[str] = []
        if not is_real:
            warnings.append("Bu veri gerçek/lisanslı kaynak olarak işaretlenmemiştir.")
        if is_derived:
            warnings.append(f"Bu veri {source_timeframe} timeframe'inden türetilmiştir.")
        return cls(
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            provider=source,
            source_type=source_type,
            is_real=is_real,
            is_derived=is_derived,
            source_timeframe=source_timeframe,
            quality_status=quality,
            coverage_pct=coverage_pct,
            fetched_at=fetched_at,
            warnings=warnings,
        )


# ─── Eski BarResponseMetadata (geriye dönük uyum) ───────────────────────────

class BarResponseMetadata(BaseModel):
    """Geriye dönük uyum — yeni kodda DataTruth kullanılmalı."""
    source:           str
    is_real:          bool
    is_derived:       bool
    source_timeframe: str
    quality_status:   str
    coverage_pct:     float

    def to_data_truth(self, symbol: str, market: str, timeframe: str) -> DataTruth:
        return DataTruth.from_bar_metadata(
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            is_real=self.is_real,
            source=self.source,
            is_derived=self.is_derived,
            source_timeframe=self.source_timeframe,
            coverage_pct=self.coverage_pct,
        )


# ─── Candle Response (v1 + v2) ───────────────────────────────────────────────

class CandleResponse(BaseModel):
    """v1 candle yanıtı — metadata yeni DataTruth'a referans verir."""
    bars:     List[Dict[str, Any]]
    metadata: BarResponseMetadata


class CandleResponseV2(BaseModel):
    """v2 candle yanıtı — DataTruth kontratını uygular."""
    bars:       List[Dict[str, Any]]
    data_truth: DataTruth
    fetched_at: str = ""

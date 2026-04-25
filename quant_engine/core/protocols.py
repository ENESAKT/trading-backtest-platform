"""
Quant Engine — Protocol Tanımları (Soyut Arayüzler)

Core katmanının dış dünyayı bilmemesi için tüm sözleşmeler
burada Protocol olarak tanımlanır.

Bağımlılık akışı:
    core ← data ← strategy ← backtest ← research ← reporting ← app/cli
    Core hiçbir şeyi import etmez. Herkes core'u import edebilir.

Kullanım:
    from quant_engine.core.protocols import (
        MarketDataProvider,
        StorageBackend,
        Strategy,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Protocol, runtime_checkable

import pandas as pd

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AssetClass(str, Enum):
    """Varlık sınıfı."""
    EQUITY = "equity"
    FUTURES = "futures"
    INDEX = "index"


class Market(str, Enum):
    """Piyasa."""
    BIST = "bist"
    VIOP = "viop"


class Timeframe(str, Enum):
    """Zaman dilimi."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1wk"
    MO1 = "1mo"


class OrderSide(str, Enum):
    """Emir yönü."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Emir tipi."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class DataLayer(str, Enum):
    """Veri katmanı."""
    RAW = "raw"
    CLEAN = "clean"
    ADJUSTED = "adjusted"
    FEATURES = "features"


# ---------------------------------------------------------------------------
# Veri Modelleri (Value Objects)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BarRequest:
    """Veri çekme isteği."""
    symbol: str
    market: Market = Market.BIST
    timeframe: Timeframe = Timeframe.D1
    start: date | None = None
    end: date | None = None


@dataclass
class FetchResult:
    """Veri çekme sonucu."""
    symbol: str
    data: pd.DataFrame
    source: str
    fetched_at: datetime = field(
        default_factory=datetime.utcnow
    )
    row_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.row_count > 0

    def __post_init__(self):
        self.row_count = len(self.data)


@dataclass(frozen=True)
class ProviderCapabilities:
    """Bir veri sağlayıcının yetenekleri."""
    name: str
    supported_markets: list[Market]
    supported_timeframes: list[Timeframe]
    supports_intraday: bool = False
    supports_live: bool = False
    max_history_days: int | None = None
    rate_limit_per_minute: int | None = None


@dataclass
class WriteResult:
    """Depolama yazma sonucu."""
    symbol: str
    layer: DataLayer
    rows_written: int = 0
    path: str = ""
    checksum: str = ""
    success: bool = True
    error: str = ""


@dataclass
class DatasetMetadata:
    """Bir dataset hakkında metadata."""
    symbol: str
    layer: DataLayer
    source: str
    row_count: int
    first_date: date | None = None
    last_date: date | None = None
    checksum: str = ""
    ingested_at: datetime | None = None
    schema_version: str = "1.0"


# ---------------------------------------------------------------------------
# Protocol Tanımları
# ---------------------------------------------------------------------------

@runtime_checkable
class MarketDataProvider(Protocol):
    """
    Veri sağlayıcı arayüzü.

    yfinance, Matriks, BIST VERDA — hepsi bunu implemente eder.
    Yeni provider eklerken motor bozulmaz.
    """

    def capabilities(self) -> ProviderCapabilities:
        """Provider'ın yeteneklerini döndür."""
        ...

    def fetch_bars(self, request: BarRequest) -> FetchResult:
        """Bar verisi çek."""
        ...

    def health_check(self) -> bool:
        """Provider erişilebilir mi?"""
        ...


@runtime_checkable
class StorageBackend(Protocol):
    """
    Depolama arayüzü.

    Parquet, DuckDB, veya başka backend — hepsi bunu implemente eder.
    """

    def read(
        self,
        symbol: str,
        timeframe: Timeframe,
        layer: DataLayer,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Veri oku."""
        ...

    def write(
        self,
        data: pd.DataFrame,
        symbol: str,
        layer: DataLayer,
        metadata: DatasetMetadata | None = None,
    ) -> WriteResult:
        """Veri yaz."""
        ...

    def list_symbols(
        self,
        market: Market,
        timeframe: Timeframe,
    ) -> list[str]:
        """Mevcut sembolleri listele."""
        ...

    def get_metadata(
        self,
        symbol: str,
        layer: DataLayer,
    ) -> DatasetMetadata | None:
        """Dataset metadata'sını döndür."""
        ...


@runtime_checkable
class Strategy(Protocol):
    """
    Strateji arayüzü.

    Tüm stratejiler bunu implemente eder.
    """

    def generate_signals(
        self,
        data: pd.DataFrame,
        params: dict,
    ) -> pd.DataFrame:
        """Sinyal üret — SignalFrame döndür."""
        ...

    def get_params(self) -> dict:
        """Strateji parametrelerini döndür."""
        ...

    def get_warm_up_bars(self) -> int:
        """Warm-up bar sayısını döndür."""
        ...


@runtime_checkable
class ExecutionModel(Protocol):
    """İşlem yürütme modeli."""

    def simulate(
        self,
        order: object,
        bar: pd.Series,
        context: dict,
    ) -> object:
        """Emir simülasyonu — Fill döndür."""
        ...


@runtime_checkable
class CostModel(Protocol):
    """Maliyet modeli."""

    def calculate(self, fill: object) -> float:
        """Maliyet hesapla."""
        ...

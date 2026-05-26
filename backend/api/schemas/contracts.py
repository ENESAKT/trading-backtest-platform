"""PiyasaPilot — Ortak API Kontrat Tipleri (Bölüm 18.14)

Bu dosya backend/frontend/Flutter arasında tek kaynak olarak kullanılır.
Her tip için karşılığı:
  - Backend : bu Pydantic modeli
  - Frontend: frontend/src/types.ts içindeki TypeScript interface'i
  - Flutter : mobile/lib/models/ altındaki Dart sınıfı

Eklenen tipler:
  ScreenerRunRequest, ScreenerRunResponse, ScreenerRow
  SymbolSnapshot
  TechnicalSummary, OscillatorEntry, MovingAverageEntry, PivotLevels
  BacktestAssumptions
  PaperOrder, PaperPosition, PaperPortfolioSummary
  SignalEvidence, SignalIndicatorSnapshot
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from backend.data.schemas.market import DataTruth


# ─── Screener ────────────────────────────────────────────────────────────────

class ScreenerFilter(BaseModel):
    """Tek bir screener filtresi."""
    field:    str
    operator: Literal["gt", "gte", "lt", "lte", "eq", "neq", "in", "not_in"]
    value:    Any


class ScreenerSort(BaseModel):
    field:     str
    direction: Literal["asc", "desc"] = "desc"


class ScreenerRunRequest(BaseModel):
    """POST /api/screener/run girdi kontratı."""
    market:        str                    = "BIST"
    universe:      List[str]              = Field(default_factory=list, description="Boşsa tüm evren")
    filters:       List[ScreenerFilter]   = Field(default_factory=list)
    columns:       List[str]              = Field(default_factory=list)
    sort:          Optional[ScreenerSort] = None
    limit:         int                    = Field(default=50, ge=1, le=500)
    snapshot_time: Optional[datetime]     = None


class ScreenerRow(BaseModel):
    """Screener sonuç satırı."""
    symbol:       str
    name:         Optional[str]  = None
    market:       str
    sector:       Optional[str]  = None
    last_price:   Optional[float] = None
    change_pct_1d: Optional[float] = None
    volume:       Optional[float] = None
    market_cap:   Optional[float] = None
    quality_badge: str            = "unknown"
    columns:      Dict[str, Any]  = Field(default_factory=dict)


class ScreenerRunResponse(BaseModel):
    """POST /api/screener/run çıktı kontratı."""
    run_id:             str
    created_at:         datetime
    filters_hash:       str
    data_snapshot_hash: str
    market:             str
    total_count:        int
    rows:               List[ScreenerRow]
    data_truth:         Optional[DataTruth] = None
    warnings:           List[str]           = Field(default_factory=list)


# ─── Symbol Snapshot ─────────────────────────────────────────────────────────

class SymbolSnapshot(BaseModel):
    """Sembol anlık durum kartı — izleme listesi ve 360 başlığı için."""
    symbol:         str
    market:         str
    name:           Optional[str]  = None
    sector:         Optional[str]  = None
    instrument_type: str           = "stock"

    # Fiyat
    last_price:      Optional[float] = None
    prev_close:      Optional[float] = None
    change_pct_1d:   Optional[float] = None
    high_52w:        Optional[float] = None
    low_52w:         Optional[float] = None

    # Seans
    session_status:  Literal["open", "closed", "pre", "post", "unknown"] = "unknown"
    last_bar_ts:     Optional[datetime] = None

    # Kalite
    data_truth:      Optional[DataTruth] = None

    # Temel
    pe_ratio:        Optional[float] = None
    pb_ratio:        Optional[float] = None
    market_cap:      Optional[float] = None
    eps_ttm:         Optional[float] = None
    dividend_yield:  Optional[float] = None

    warnings:        List[str] = Field(default_factory=list)


# ─── Technical Summary ───────────────────────────────────────────────────────

class OscillatorEntry(BaseModel):
    name:    str
    value:   Optional[float] = None
    signal:  Literal["buy", "sell", "neutral", "unknown"] = "unknown"
    threshold_low:  Optional[float] = None
    threshold_high: Optional[float] = None
    description:    str = ""


class MovingAverageEntry(BaseModel):
    name:         str
    period:       int
    ma_type:      Literal["ema", "sma", "wma", "vwma", "hull", "ichimoku"] = "ema"
    value:        Optional[float] = None
    signal:       Literal["above", "below", "unknown"] = "unknown"
    distance_pct: Optional[float] = None


class PivotLevels(BaseModel):
    method:  Literal["classic", "fibonacci", "camarilla", "woodie", "demark"]
    period:  str   = "1d"
    r3:      Optional[float] = None
    r2:      Optional[float] = None
    r1:      Optional[float] = None
    pp:      Optional[float] = None
    s1:      Optional[float] = None
    s2:      Optional[float] = None
    s3:      Optional[float] = None


class TechnicalSummary(BaseModel):
    """GET /api/technical/summary çıktı kontratı."""
    symbol:    str
    market:    str
    timeframe: str

    # Özet puanlar
    overall_rating:       Literal["strong_buy", "buy", "neutral", "sell", "strong_sell", "unknown"] = "unknown"
    oscillator_rating:    Literal["strong_buy", "buy", "neutral", "sell", "strong_sell", "unknown"] = "unknown"
    moving_average_rating: Literal["strong_buy", "buy", "neutral", "sell", "strong_sell", "unknown"] = "unknown"

    oscillators:     List[OscillatorEntry]    = Field(default_factory=list)
    moving_averages: List[MovingAverageEntry] = Field(default_factory=list)
    pivot_levels:    List[PivotLevels]        = Field(default_factory=list)

    warmup_bars_used:    int = 0
    calculation_version: str = "1.0"
    data_truth:          Optional[DataTruth] = None
    calculated_at:       Optional[datetime]  = None

    warnings: List[str] = Field(default_factory=list)


# ─── Backtest Assumptions ────────────────────────────────────────────────────

class BacktestAssumptions(BaseModel):
    """Backtest raporuna eklenmesi zorunlu varsayımlar kartı.

    Rapor bu kart olmadan "tamamlandı" sayılmaz (Bölüm 18.6).
    """
    data_source:         str
    data_delay_minutes:  int  = 0
    is_real_data:        bool = False

    commission_model:    Literal["fixed_bps", "fixed_pct", "tiered", "zero"] = "fixed_bps"
    commission_value:    float = 10.0
    commission_note:     str   = ""

    slippage_model:      Literal[
        "fixed_bps", "fixed_tick", "spread", "atr",
        "volume_pct", "gap_open", "low_liquidity", "zero"
    ] = "fixed_bps"
    slippage_value:      float = 5.0
    slippage_note:       str   = ""

    order_type:          Literal["market", "limit", "close"] = "market"
    execution_time:      Literal["next_open", "close", "same_bar"] = "next_open"

    corporate_action_adjusted: bool = False
    survivorship_bias_free:    bool = False
    liquidity_capacity_try:    Optional[float] = None

    data_truth: Optional[DataTruth] = None
    warnings:   List[str]           = Field(default_factory=list)


# ─── Paper Trading ───────────────────────────────────────────────────────────

class PaperOrder(BaseModel):
    """Tek bir paper emir."""
    id:             int
    strategy_id:    str
    symbol:         str
    side:           Literal["buy", "sell", "short", "cover"]
    order_type:     Literal["market", "limit", "stop"] = "market"
    status:         Literal["pending", "filled", "cancelled", "rejected"] = "filled"
    quantity:       float
    requested_price: Optional[float] = None
    filled_price:    Optional[float] = None
    created_at:     datetime
    filled_at:      Optional[datetime] = None
    reason:         str = ""


class PaperPosition(BaseModel):
    """Açık paper pozisyon."""
    strategy_id:   str
    symbol:        str
    side:          Literal["long", "short"] = "long"
    quantity:      float
    entry_price:   float
    current_price: Optional[float] = None

    # PnL
    unrealized_pnl:     Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    realized_pnl:       float           = 0.0

    opened_at:  datetime
    trade_id:   int


class PaperPortfolioSummary(BaseModel):
    """Paper cüzdan ve portföy özeti."""
    strategy_id:     str
    initial_capital: float
    cash:            float
    positions_value: float
    total_equity:    float
    unrealized_pnl:  float
    realized_pnl:    float
    daily_pnl:       float
    daily_pnl_pct:   float
    is_halted:       bool

    positions: List[PaperPosition]      = Field(default_factory=list)
    open_orders: List[PaperOrder]       = Field(default_factory=list)

    as_of: Optional[datetime] = None


# ─── Signal Evidence ─────────────────────────────────────────────────────────

class SignalIndicatorSnapshot(BaseModel):
    """Sinyal anındaki tek bir gösterge değeri."""
    name:    str
    value:   Optional[float] = None
    signal:  str             = ""
    note:    str             = ""


class SignalEvidence(BaseModel):
    """Bir sinyalin arkasındaki kanıt paketi.

    Her sinyal, backtest ve paper trading olayı için üretilmeli.
    "Neden bu sinyal üretildi?" sorusunu cevaplaması gerekir.
    """
    signal_id:      str
    strategy_id:    str
    symbol:         str
    market:         str
    timeframe:      str

    signal_type:    Literal["BUY", "SELL", "SHORT", "COVER", "HOLD"]
    strength:       int   = Field(default=5, ge=1, le=10)
    price_at_signal: float
    ts:             datetime

    # Kanıtlar
    indicators:     List[SignalIndicatorSnapshot] = Field(default_factory=list)
    reason:         str = ""
    rule_triggered: str = ""

    # Veri kalitesi
    data_truth:     Optional[DataTruth] = None

    # Uyarı / sorumluluk reddi
    disclaimer: str = "Bu sinyal yatırım tavsiyesi değildir. Teknik gösterge durumunu özetler."
    warnings:   List[str] = Field(default_factory=list)


# ─── __all__ ─────────────────────────────────────────────────────────────────

__all__ = [
    # Screener
    "ScreenerFilter",
    "ScreenerSort",
    "ScreenerRunRequest",
    "ScreenerRow",
    "ScreenerRunResponse",
    # Symbol
    "SymbolSnapshot",
    # Technical
    "OscillatorEntry",
    "MovingAverageEntry",
    "PivotLevels",
    "TechnicalSummary",
    # Backtest
    "BacktestAssumptions",
    # Paper
    "PaperOrder",
    "PaperPosition",
    "PaperPortfolioSummary",
    # Signal
    "SignalIndicatorSnapshot",
    "SignalEvidence",
]

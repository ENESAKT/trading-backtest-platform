"""
Quant Engine — Core Domain Nesneleri

Order, Fill, Position, Portfolio, CompletedTrade — backtest motorunun
temel yapı taşları.

Execution Spec:
    - bar[t].close sinyal üret → bar[t+1].open execute et
    - Anti-leakage: feature_ts ≤ decision_ts < execution_ts
    - Invariant: cash + sum(position_values) == total_equity (her barda)

Enum'lar core/protocols.py'den import edilir (tek kaynak prensibi).
Bu modülden de erişilebilir kalır (geriye dönük uyumluluk).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

# Enum'lar tek kaynaktan import edilir — core/protocols.py
from quant_engine.core.protocols import (
    OrderSide,
    OrderStatus,
    OrderType,
)

# Geriye dönük uyumluluk: bu modülden import edenler çalışmaya devam eder
__all__ = [
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "Order",
    "Fill",
    "Position",
    "Portfolio",
    "EquityPoint",
    "CompletedTrade",
]


@dataclass
class Order:
    """Emir nesnesi."""

    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    signal_bar_index: int = 0
    signal_timestamp: Optional[dt.datetime] = None
    execution_bar_index: int = 0
    execution_timestamp: Optional[dt.datetime] = None
    status: OrderStatus = OrderStatus.PENDING
    order_id: str = ""


@dataclass
class Fill:
    """Emir dolum sonucu."""

    order: Order
    fill_price: float
    fill_quantity: int
    commission: float = 0.0
    slippage: float = 0.0
    slippage_cost: float = 0.0  # slippage * quantity (gerçek maliyet etkisi)
    fill_timestamp: Optional[dt.datetime] = None
    bar_index: int = 0

    @property
    def total_cost(self) -> float:
        """Toplam maliyet (fiyat * miktar + komisyon)."""
        return (
            self.fill_price * self.fill_quantity
            + self.commission
        )

    @property
    def net_amount(self) -> float:
        """
        Net tutar (alım/satım yönüne göre).
        Alım: negatif (nakit azalır)
        Satım: pozitif (nakit artar)
        """
        base = self.fill_price * self.fill_quantity
        if self.order.side == OrderSide.BUY:
            return -(base + self.commission)
        return base - self.commission


@dataclass
class CompletedTrade:
    """
    Tamamlanmış bir al-sat çifti.

    Her trade bir buy fill + sell fill eşleşmesidir.
    Metrikler bu nesnelerden hesaplanır.
    """

    symbol: str
    entry_date: Optional[dt.datetime] = None
    exit_date: Optional[dt.datetime] = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: int = 0
    side: OrderSide = OrderSide.BUY  # Long trade
    entry_bar_index: int = 0
    exit_bar_index: int = 0
    entry_commission: float = 0.0
    exit_commission: float = 0.0
    entry_slippage_cost: float = 0.0
    exit_slippage_cost: float = 0.0

    @property
    def gross_pnl(self) -> float:
        """Brüt kar/zarar (komisyon/slippage öncesi)."""
        return (self.exit_price - self.entry_price) * self.quantity

    @property
    def total_commission(self) -> float:
        """Toplam komisyon."""
        return self.entry_commission + self.exit_commission

    @property
    def total_slippage_cost(self) -> float:
        """Toplam slippage maliyeti."""
        return self.entry_slippage_cost + self.exit_slippage_cost

    @property
    def net_pnl(self) -> float:
        """Net kar/zarar (komisyon + slippage sonrası)."""
        return self.gross_pnl - self.total_commission

    @property
    def pnl_pct(self) -> float:
        """Net PnL yüzdesi."""
        cost_basis = self.entry_price * self.quantity
        if cost_basis == 0:
            return 0.0
        return (self.net_pnl / cost_basis) * 100

    @property
    def holding_bars(self) -> int:
        """Pozisyonun tutulduğu bar sayısı."""
        return self.exit_bar_index - self.entry_bar_index

    @property
    def is_winner(self) -> bool:
        """Kazançlı trade mi?"""
        return self.net_pnl > 0


@dataclass
class Position:
    """Açık pozisyon."""

    symbol: str
    quantity: int = 0
    avg_entry_price: float = 0.0
    total_cost_basis: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.quantity != 0

    def market_value(self, current_price: float) -> float:
        """Mevcut piyasa değeri."""
        return self.quantity * current_price

    def unrealized_pnl(
        self, current_price: float
    ) -> float:
        """Gerçekleşmemiş kar/zarar."""
        if self.quantity == 0:
            return 0.0
        return (
            (current_price - self.avg_entry_price)
            * self.quantity
        )

    def update_on_fill(self, fill: Fill) -> float:
        """
        Fill ile pozisyonu güncelle. (Short selling ve reversal destekler)

        Returns:
            float: Gerçekleşen PnL
        """
        realized_pnl = 0.0
        fill_qty = fill.fill_quantity if fill.order.side == OrderSide.BUY else -fill.fill_quantity

        # Eğer miktar 0 ise veya yön aynıysa -> direkt ekle
        if self.quantity == 0 or (self.quantity > 0 and fill_qty > 0) or (self.quantity < 0 and fill_qty < 0):
            new_qty = self.quantity + fill_qty
            new_cost = self.total_cost_basis + fill.fill_price * abs(fill_qty)
            self.quantity = new_qty
            self.total_cost_basis = new_cost
            self.avg_entry_price = new_cost / abs(new_qty)
            return 0.0

        # Ters yöndeyse -> pozisyon kapanıyor veya yön değiştiriyor
        if abs(fill_qty) <= abs(self.quantity):
            # Tamamı mevcut pozisyonu kapatmaya harcanıyor (reversal yok)
            if self.quantity > 0:  # Long pozisyonu kapatıyor
                realized_pnl = (fill.fill_price - self.avg_entry_price) * abs(fill_qty)
            else:  # Short pozisyonu kapatıyor
                realized_pnl = (self.avg_entry_price - fill.fill_price) * abs(fill_qty)

            self.quantity += fill_qty
            if self.quantity == 0:
                self.total_cost_basis = 0.0
                self.avg_entry_price = 0.0
            else:
                self.total_cost_basis = self.avg_entry_price * abs(self.quantity)
        else:
            # Reversal durumu (mevcut pozisyon tamamen kapanıyor, kalanıyla yeni yön açılıyor)
            closed_qty = abs(self.quantity)
            if self.quantity > 0:  # Long'dan Short'a dönüş
                realized_pnl = (fill.fill_price - self.avg_entry_price) * closed_qty
            else:  # Short'dan Long'a dönüş
                realized_pnl = (self.avg_entry_price - fill.fill_price) * closed_qty

            # Yeni pozisyon kalan miktarla açılıyor
            remaining_qty = fill_qty + self.quantity  # işaretleri doğru topluyoruz
            self.quantity = remaining_qty
            self.total_cost_basis = fill.fill_price * abs(remaining_qty)
            self.avg_entry_price = fill.fill_price

        return realized_pnl


@dataclass
class Portfolio:
    """Portföy durumu."""

    initial_capital: float = 100_000.0
    cash: float = 0.0
    positions: dict[str, Position] = field(
        default_factory=dict
    )
    realized_pnl: float = 0.0
    total_commission: float = 0.0

    def __post_init__(self):
        if self.cash == 0.0:
            self.cash = self.initial_capital

    def total_equity(
        self, prices: dict[str, float]
    ) -> float:
        """
        Toplam özvarlık = nakit + pozisyon değerleri.

        INVARIANT: Bu değer her barda tutarlı olmalı.
        """
        position_value = sum(
            pos.market_value(prices.get(sym, 0.0))
            for sym, pos in self.positions.items()
            if pos.is_open
        )
        return self.cash + position_value

    def total_position_value(
        self, prices: dict[str, float]
    ) -> float:
        """Toplam pozisyon değeri."""
        return sum(
            pos.market_value(prices.get(sym, 0.0))
            for sym, pos in self.positions.items()
            if pos.is_open
        )

    def exposure(
        self, prices: dict[str, float]
    ) -> float:
        """Portföy exposure (pozisyon/equity)."""
        equity = self.total_equity(prices)
        if equity == 0:
            return 0.0
        return self.total_position_value(prices) / equity

    def get_or_create_position(
        self, symbol: str
    ) -> Position:
        """Pozisyon al veya oluştur."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def process_fill(self, fill: Fill) -> float:
        """
        Fill'i portföye uygula.

        Returns:
            float: Gerçekleşen PnL
        """
        position = self.get_or_create_position(
            fill.order.symbol
        )

        # Nakit güncelle
        self.cash += fill.net_amount

        # Pozisyon güncelle
        realized = position.update_on_fill(fill)
        self.realized_pnl += realized
        self.total_commission += fill.commission

        return realized


@dataclass
class EquityPoint:
    """Tek bir zaman noktasındaki portföy durumu."""

    timestamp: dt.datetime
    bar_index: int
    cash: float
    position_value: float
    total_equity: float
    drawdown: float = 0.0
    drawdown_pct: float = 0.0

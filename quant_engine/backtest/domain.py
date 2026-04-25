"""
Quant Engine — Core Domain Nesneleri

Order, Fill, Position, Portfolio — backtest motorunun temel yapı taşları.

Execution Spec:
    - bar[t].close sinyal üret → bar[t+1].open execute et
    - Anti-leakage: feature_ts ≤ decision_ts < execution_ts
    - Invariant: cash + sum(position_values) == total_equity (her barda)
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


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
        Fill ile pozisyonu güncelle.

        Returns:
            float: Gerçekleşen PnL (pozisyon kapanırsa)
        """
        realized_pnl = 0.0

        if fill.order.side == OrderSide.BUY:
            # Toplam maliyet güncelle
            new_cost = (
                self.total_cost_basis
                + fill.fill_price * fill.fill_quantity
            )
            self.quantity += fill.fill_quantity
            self.total_cost_basis = new_cost
            if self.quantity > 0:
                self.avg_entry_price = (
                    new_cost / self.quantity
                )
        else:
            # Satışta realized PnL hesapla
            realized_pnl = (
                (fill.fill_price - self.avg_entry_price)
                * fill.fill_quantity
            )
            self.quantity -= fill.fill_quantity
            if self.quantity > 0:
                self.total_cost_basis = (
                    self.avg_entry_price * self.quantity
                )
            else:
                self.total_cost_basis = 0.0
                self.avg_entry_price = 0.0

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

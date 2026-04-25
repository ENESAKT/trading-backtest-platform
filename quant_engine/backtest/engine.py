"""
Quant Engine — Backtest Engine

Minimal backtest motoru. Tek sembol, long-only, market order.

Execution Spec:
    1. bar[t].close'da sinyal üret
    2. bar[t+1].open'da execute et (lookahead bias yok)
    3. Her barda portfolio invariant doğrula
    4. Audit trail: signal → order → fill → position → pnl

Kullanım:
    from quant_engine.backtest.engine import BacktestEngine

    engine = BacktestEngine(config)
    result = engine.run(data, signal_func)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger

from quant_engine.backtest.domain import (
    EquityPoint,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
)


@dataclass
class BacktestConfig:
    """Backtest çalıştırma konfigürasyonu."""
    initial_capital: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: int = 5
    max_position_pct: float = 0.20
    warm_up_bars: int = 0


@dataclass
class BacktestResult:
    """Backtest sonucu."""
    equity_curve: list[EquityPoint] = field(
        default_factory=list
    )
    orders: list[Order] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    final_equity: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    total_commission: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0


class BacktestEngine:
    """
    Minimal backtest motoru.

    Signal function imzası:
        def signal_func(
            data: pd.DataFrame,
            bar_index: int,
            portfolio: Portfolio,
        ) -> int:
            # +1 = al, -1 = sat, 0 = bekle
            return 0

    Invariant: cash + position_value == total_equity (her bar)
    """

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def _calculate_slippage(
        self, price: float, side: OrderSide
    ) -> float:
        """Slippage hesapla (baz puan)."""
        slippage_pct = self.config.slippage_bps / 10_000
        if side == OrderSide.BUY:
            return price * (1 + slippage_pct)
        return price * (1 - slippage_pct)

    def _calculate_commission(
        self, price: float, quantity: int
    ) -> float:
        """Komisyon hesapla."""
        return price * quantity * self.config.commission_rate

    def _calculate_position_size(
        self,
        portfolio: Portfolio,
        price: float,
        prices: dict[str, float],
    ) -> int:
        """
        Pozisyon büyüklüğü hesapla.

        max_position_pct ile sınırlandırılmış.
        """
        equity = portfolio.total_equity(prices)
        max_value = equity * self.config.max_position_pct
        # Komisyon ve slippage için %1 marj bırak
        available = min(portfolio.cash * 0.99, max_value)
        if price <= 0:
            return 0
        quantity = int(available / price)
        return max(0, quantity)

    def run(
        self,
        data: pd.DataFrame,
        signal_func,
        symbol: str = "UNKNOWN",
    ) -> BacktestResult:
        """
        Backtest çalıştır.

        Args:
            data: OHLCV verisi (date, open, high, low,
                  close, volume sütunları)
            signal_func: Sinyal fonksiyonu
                (data, bar_index, portfolio) → int
            symbol: Sembol adı

        Returns:
            BacktestResult: Backtest sonucu
        """
        if data.empty or len(data) < 2:
            logger.error("Yetersiz veri!")
            return BacktestResult()

        # Sıralı veri garantile
        data = data.sort_values("date").reset_index(
            drop=True
        )

        portfolio = Portfolio(
            initial_capital=self.config.initial_capital
        )
        result = BacktestResult()
        peak_equity = self.config.initial_capital
        pending_signal: int = 0

        logger.info(
            f"🚀 Backtest: {symbol} | "
            f"{len(data)} bar | "
            f"₺{self.config.initial_capital:,.0f} sermaye"
        )

        for i in range(len(data)):
            bar = data.iloc[i]
            current_price = float(bar["close"])
            current_open = float(bar["open"])
            prices = {symbol: current_price}
            bar_date = pd.Timestamp(bar["date"])

            # --- EXECUTION PHASE ---
            # Önceki bardan gelen sinyali bu barın
            # open'ında execute et
            if i > 0 and pending_signal != 0:
                fill = self._execute_signal(
                    pending_signal,
                    symbol,
                    current_open,
                    portfolio,
                    prices,
                    i,
                    bar_date,
                )
                if fill:
                    realized = portfolio.process_fill(fill)
                    result.orders.append(fill.order)
                    result.fills.append(fill)
                    if realized != 0:
                        result.total_trades += 1

                pending_signal = 0

            # --- SIGNAL PHASE ---
            # Warm-up kontrolü
            if i < self.config.warm_up_bars:
                signal = 0
            else:
                # bar[t].close'da sinyal üret
                signal = signal_func(data, i, portfolio)

            pending_signal = signal

            # --- EQUITY TRACKING ---
            equity = portfolio.total_equity(prices)
            pos_value = portfolio.total_position_value(
                prices
            )

            # Portfolio invariant doğrula
            expected = portfolio.cash + pos_value
            if abs(equity - expected) > 0.01:
                logger.error(
                    f"❌ Bar {i}: Invariant kırıldı! "
                    f"equity={equity:.2f} != "
                    f"cash+pos={expected:.2f}"
                )

            # Drawdown hesapla
            peak_equity = max(peak_equity, equity)
            drawdown = peak_equity - equity
            dd_pct = (
                (drawdown / peak_equity * 100)
                if peak_equity > 0
                else 0.0
            )

            result.equity_curve.append(
                EquityPoint(
                    timestamp=bar_date.to_pydatetime(),
                    bar_index=i,
                    cash=portfolio.cash,
                    position_value=pos_value,
                    total_equity=equity,
                    drawdown=drawdown,
                    drawdown_pct=dd_pct,
                )
            )

        # --- SON DURUM ---
        final_prices = {
            symbol: float(data.iloc[-1]["close"])
        }
        result.final_equity = portfolio.total_equity(
            final_prices
        )
        result.total_return_pct = (
            (
                result.final_equity
                / self.config.initial_capital
                - 1
            )
            * 100
        )
        result.max_drawdown_pct = (
            max(
                ep.drawdown_pct
                for ep in result.equity_curve
            )
            if result.equity_curve
            else 0.0
        )
        result.total_commission = portfolio.total_commission

        # Sharpe Ratio (günlük)
        if len(result.equity_curve) > 1:
            equities = [
                ep.total_equity
                for ep in result.equity_curve
            ]
            returns = pd.Series(equities).pct_change().dropna()
            if returns.std() > 0:
                result.sharpe_ratio = (
                    returns.mean() / returns.std()
                ) * (252 ** 0.5)

        # Win rate — al/sat çiftlerinden hesapla
        buy_fills = [
            f for f in result.fills
            if f.order.side == OrderSide.BUY
        ]
        sell_fills = [
            f for f in result.fills
            if f.order.side == OrderSide.SELL
        ]
        if sell_fills:
            profitable = 0
            for sell_fill in sell_fills:
                # Eşleşen buy'ı bul (aynı sembol, sell'den önce)
                matching_buys = [
                    b for b in buy_fills
                    if b.order.symbol == sell_fill.order.symbol
                    and b.bar_index < sell_fill.bar_index
                ]
                if matching_buys:
                    last_buy = matching_buys[-1]
                    if sell_fill.fill_price > last_buy.fill_price:
                        profitable += 1
            result.win_rate = profitable / len(sell_fills)

        logger.success(
            f"✅ Backtest tamamlandı: "
            f"₺{result.final_equity:,.0f} "
            f"({result.total_return_pct:+.2f}%) | "
            f"Max DD: {result.max_drawdown_pct:.2f}% | "
            f"Sharpe: {result.sharpe_ratio:.2f}"
        )

        return result

    def _execute_signal(
        self,
        signal: int,
        symbol: str,
        open_price: float,
        portfolio: Portfolio,
        prices: dict[str, float],
        bar_index: int,
        bar_date: pd.Timestamp,
    ) -> Fill | None:
        """Sinyali execute et."""
        position = portfolio.get_or_create_position(symbol)

        if signal > 0 and not position.is_open:
            # AL sinyali — pozisyon yok
            side = OrderSide.BUY
            fill_price = self._calculate_slippage(
                open_price, side
            )
            quantity = self._calculate_position_size(
                portfolio, fill_price, prices
            )
            if quantity <= 0:
                return None

        elif signal < 0 and position.is_open:
            # SAT sinyali — pozisyon var
            side = OrderSide.SELL
            fill_price = self._calculate_slippage(
                open_price, side
            )
            quantity = position.quantity

        else:
            return None

        commission = self._calculate_commission(
            fill_price, quantity
        )

        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            signal_bar_index=bar_index - 1,
            signal_timestamp=bar_date.to_pydatetime(),
            status=OrderStatus.FILLED,
            order_id=f"{symbol}_{bar_index}_{side.value}",
        )

        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=quantity,
            commission=commission,
            slippage=abs(fill_price - open_price),
            fill_timestamp=bar_date.to_pydatetime(),
            bar_index=bar_index,
        )

        logger.debug(
            f"📊 {bar_date:%Y-%m-%d} | "
            f"{side.value.upper()} {quantity}x "
            f"{symbol} @ {fill_price:.2f} | "
            f"Komisyon: ₺{commission:.2f}"
        )

        return fill


def buy_and_hold_signal(
    data: pd.DataFrame,
    bar_index: int,
    portfolio: Portfolio,
) -> int:
    """
    Buy & Hold baseline stratejisi.

    İlk barda al, son bara kadar tut.
    """
    position = portfolio.get_or_create_position(
        data.iloc[bar_index].get("symbol", "UNKNOWN")
    )
    if bar_index == 0 and not position.is_open:
        return 1  # AL
    return 0  # BEKLE

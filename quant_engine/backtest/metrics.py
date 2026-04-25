"""
Quant Engine — Performans Metrikleri

Backtest sonuçlarından performans metrikleri hesaplar.

Metrikler:
    - Total Return (%)
    - CAGR (Yıllık Bileşik Getiri)
    - Max Drawdown (%)
    - Sharpe Ratio (günlük → yıllık)
    - Sortino Ratio
    - Calmar Ratio
    - Win Rate
    - Profit Factor
    - Average Holding Period
    - Gross vs Net Performance

Kullanım:
    from quant_engine.backtest.metrics import calculate_metrics

    metrics = calculate_metrics(result)
    print(metrics["sharpe_ratio"])
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from quant_engine.backtest.domain import EquityPoint, Fill, OrderSide


@dataclass
class PerformanceMetrics:
    """Tüm performans metrikleri."""

    # Getiri
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    annualized_return_pct: float = 0.0

    # Risk
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0
    volatility_annual: float = 0.0

    # Risk-Adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Maliyet
    total_commission: float = 0.0
    total_slippage: float = 0.0
    gross_return_pct: float = 0.0
    net_return_pct: float = 0.0

    # Diğer
    exposure_pct: float = 0.0
    avg_holding_bars: float = 0.0
    trade_count: int = 0
    initial_capital: float = 0.0
    final_equity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Dictionary'e çevir."""
        return {
            k: round(v, 4) if isinstance(v, float) else v
            for k, v in self.__dict__.items()
        }

    def summary(self) -> str:
        """Okunabilir özet."""
        lines = [
            "═" * 50,
            "  PERFORMANS METRİKLERİ",
            "═" * 50,
            f"  Başlangıç:     ₺{self.initial_capital:>15,.2f}",
            f"  Son Değer:     ₺{self.final_equity:>15,.2f}",
            f"  Toplam Getiri: {self.total_return_pct:>14.2f}%",
            f"  CAGR:          {self.cagr_pct:>14.2f}%",
            "─" * 50,
            f"  Max Drawdown:  {self.max_drawdown_pct:>14.2f}%",
            f"  Volatilite:    {self.volatility_annual:>14.2f}%",
            f"  Sharpe:        {self.sharpe_ratio:>14.2f}",
            f"  Sortino:       {self.sortino_ratio:>14.2f}",
            f"  Calmar:        {self.calmar_ratio:>14.2f}",
            "─" * 50,
            f"  Toplam Trade:  {self.total_trades:>14d}",
            f"  Win Rate:      {self.win_rate:>14.2f}%",
            f"  Profit Factor: {self.profit_factor:>14.2f}",
            f"  Ort. Kazanç:   ₺{self.avg_win:>14,.2f}",
            f"  Ort. Kayıp:    ₺{self.avg_loss:>14,.2f}",
            "─" * 50,
            f"  Komisyon:      ₺{self.total_commission:>14,.2f}",
            f"  Slippage:      ₺{self.total_slippage:>14,.2f}",
            f"  Brüt Getiri:   {self.gross_return_pct:>14.2f}%",
            f"  Net Getiri:    {self.net_return_pct:>14.2f}%",
            "═" * 50,
        ]
        return "\n".join(lines)


def calculate_metrics(
    equity_curve: list[EquityPoint],
    fills: list[Fill],
    initial_capital: float,
    trading_days_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> PerformanceMetrics:
    """
    Backtest sonucundan performans metrikleri hesapla.

    Args:
        equity_curve: Equity curve noktaları
        fills: Dolum listesi
        initial_capital: Başlangıç sermayesi
        trading_days_per_year: Yıllık işlem günü (varsayılan 252)
        risk_free_rate: Risksiz faiz oranı (yıllık, varsayılan 0)

    Returns:
        PerformanceMetrics: Tüm metrikler
    """
    metrics = PerformanceMetrics(initial_capital=initial_capital)

    if not equity_curve:
        return metrics

    # --- Equity serisini hazırla ---
    equities = pd.Series(
        [ep.total_equity for ep in equity_curve]
    )
    final_equity = equities.iloc[-1]
    metrics.final_equity = final_equity
    n_bars = len(equities)

    # --- Getiri ---
    metrics.total_return_pct = (
        (final_equity / initial_capital - 1) * 100
    )
    metrics.net_return_pct = metrics.total_return_pct

    # CAGR
    if n_bars > 1:
        years = n_bars / trading_days_per_year
        if years > 0 and final_equity > 0:
            metrics.cagr_pct = (
                ((final_equity / initial_capital) ** (1 / years) - 1) * 100
            )
            metrics.annualized_return_pct = metrics.cagr_pct

    # --- Günlük getiriler ---
    daily_returns = equities.pct_change().dropna()

    if len(daily_returns) > 1:
        # Volatilite (yıllık)
        metrics.volatility_annual = (
            daily_returns.std() * np.sqrt(trading_days_per_year) * 100
        )

        # Sharpe Ratio
        daily_rf = risk_free_rate / trading_days_per_year
        excess_returns = daily_returns - daily_rf
        if daily_returns.std() > 0:
            metrics.sharpe_ratio = (
                excess_returns.mean() / daily_returns.std()
            ) * np.sqrt(trading_days_per_year)

        # Sortino Ratio (sadece negatif getirilerle)
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            if downside_std > 0:
                metrics.sortino_ratio = (
                    excess_returns.mean() / downside_std
                ) * np.sqrt(trading_days_per_year)

    # --- Drawdown ---
    metrics.max_drawdown_pct = max(
        (ep.drawdown_pct for ep in equity_curve), default=0.0
    )

    # Max drawdown süresi (bar sayısı)
    if equity_curve:
        max_dd_duration = 0
        current_dd_duration = 0
        for ep in equity_curve:
            if ep.drawdown > 0:
                current_dd_duration += 1
                max_dd_duration = max(
                    max_dd_duration, current_dd_duration
                )
            else:
                current_dd_duration = 0
        metrics.max_drawdown_duration_days = max_dd_duration

    # Calmar Ratio
    if metrics.max_drawdown_pct > 0:
        metrics.calmar_ratio = (
            metrics.cagr_pct / metrics.max_drawdown_pct
        )

    # --- Trade İstatistikleri ---
    buy_fills = [
        f for f in fills if f.order.side == OrderSide.BUY
    ]
    sell_fills = [
        f for f in fills if f.order.side == OrderSide.SELL
    ]

    # Trade PnL hesapla (her al-sat çifti bir trade)
    trade_pnls: list[float] = []
    for sell in sell_fills:
        matching_buys = [
            b for b in buy_fills
            if b.order.symbol == sell.order.symbol
            and b.bar_index < sell.bar_index
        ]
        if matching_buys:
            buy = matching_buys[-1]
            pnl = (
                (sell.fill_price - buy.fill_price)
                * sell.fill_quantity
                - sell.commission
                - buy.commission
            )
            trade_pnls.append(pnl)

    metrics.total_trades = len(trade_pnls)
    metrics.trade_count = len(trade_pnls)

    if trade_pnls:
        wins = [p for p in trade_pnls if p > 0]
        losses = [p for p in trade_pnls if p <= 0]

        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.win_rate = (
            len(wins) / len(trade_pnls) * 100
        )

        if wins:
            metrics.avg_win = sum(wins) / len(wins)
            metrics.largest_win = max(wins)
        if losses:
            metrics.avg_loss = sum(losses) / len(losses)
            metrics.largest_loss = min(losses)

        # Profit Factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        if gross_loss > 0:
            metrics.profit_factor = gross_profit / gross_loss

        # Gross return (komisyon öncesi)
        total_commission = sum(f.commission for f in fills)
        total_slippage = sum(f.slippage for f in fills)
        metrics.total_commission = total_commission
        metrics.total_slippage = total_slippage
        metrics.gross_return_pct = (
            (final_equity + total_commission)
            / initial_capital - 1
        ) * 100

    # --- Holding Period ---
    if buy_fills and sell_fills:
        holding_bars: list[int] = []
        for sell in sell_fills:
            matching_buys = [
                b for b in buy_fills
                if b.order.symbol == sell.order.symbol
                and b.bar_index < sell.bar_index
            ]
            if matching_buys:
                buy = matching_buys[-1]
                holding_bars.append(
                    sell.bar_index - buy.bar_index
                )
        if holding_bars:
            metrics.avg_holding_bars = (
                sum(holding_bars) / len(holding_bars)
            )

    # --- Exposure ---
    if equity_curve:
        exposed_bars = sum(
            1 for ep in equity_curve if ep.position_value > 0
        )
        metrics.exposure_pct = (
            exposed_bars / len(equity_curve) * 100
        )

    return metrics

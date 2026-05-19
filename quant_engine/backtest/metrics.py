"""
Quant Engine — Performans Metrikleri

Backtest sonuçlarından performans metrikleri hesaplar.

Düzeltmeler (Aşama 3):
    - CAGR gerçek tarih farkından hesaplanır (bar sayısından değil)
    - Sharpe/Sortino timeframe-aware (günlük/haftalık/aylık/saatlik)
    - Slippage toplamı adet ile çarpılmış maliyet etkisi
    - Trade metrikleri CompletedTrade nesnelerinden hesaplanır
    - Yanlış timeframe'de uyarı verilir
    - Gross/net return net ayrımı doğru

Metrikler:
    - Total Return (%)
    - CAGR (Yıllık Bileşik Getiri — gerçek tarih farkından)
    - Max Drawdown (%, süre)
    - Sharpe Ratio (timeframe-aware)
    - Sortino Ratio
    - Calmar Ratio
    - Win Rate, Profit Factor
    - Average Holding Period
    - Gross vs Net Performance

Kullanım:
    from quant_engine.backtest.metrics import calculate_metrics

    metrics = calculate_metrics(result)
    print(metrics["sharpe_ratio"])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from quant_engine.backtest.domain import (
    CompletedTrade,
    EquityPoint,
    Fill,
    OrderSide,
)

# --- Timeframe → yıllık çarpan eşleme ---
_ANNUALIZATION_FACTORS: dict[str, float] = {
    "1m": 252 * 390,   # ~98,280 dakika/yıl
    "5m": 252 * 78,    # ~19,656
    "15m": 252 * 26,   # ~6,552
    "30m": 252 * 13,   # ~3,276
    "1h": 252 * 6.5,   # ~1,638
    "4h": 252 * 1.625,  # ~409.5
    "1d": 252,
    "1wk": 52,
    "1mo": 12,
}


def _get_annualization_factor(
    timeframe: str = "1d",
) -> float:
    """Timeframe'e göre annualization çarpanı döndür."""
    factor = _ANNUALIZATION_FACTORS.get(timeframe)
    if factor is None:
        logger.warning(
            f"⚠️ Bilinmeyen timeframe: '{timeframe}', "
            f"günlük (252) varsayılıyor."
        )
        return 252.0
    return factor


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
    total_slippage_cost: float = 0.0
    gross_return_pct: float = 0.0
    net_return_pct: float = 0.0

    # Diğer
    exposure_pct: float = 0.0
    avg_holding_bars: float = 0.0
    trade_count: int = 0
    initial_capital: float = 0.0
    final_equity: float = 0.0
    timeframe: str = "1d"
    has_open_position: bool = False

    # Uyarılar
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Dictionary'e çevir."""
        return {
            k: round(v, 4) if isinstance(v, float) else v
            for k, v in self.__dict__.items()
            if k != "warnings"
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
            f"  DD Süresi:     {self.max_drawdown_duration_days:>14d} bar",
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
            f"  En B. Kazanç:  ₺{self.largest_win:>14,.2f}",
            f"  En B. Kayıp:   ₺{self.largest_loss:>14,.2f}",
            "─" * 50,
            f"  Komisyon:      ₺{self.total_commission:>14,.2f}",
            f"  Slippage:      ₺{self.total_slippage_cost:>14,.2f}",
            f"  Brüt Getiri:   {self.gross_return_pct:>14.2f}%",
            f"  Net Getiri:    {self.net_return_pct:>14.2f}%",
            f"  Exposure:      {self.exposure_pct:>14.2f}%",
            f"  Timeframe:     {self.timeframe:>14s}",
            "═" * 50,
        ]
        if self.warnings:
            lines.append("  ⚠️ UYARILAR:")
            for w in self.warnings:
                lines.append(f"    - {w}")
            lines.append("═" * 50)
        return "\n".join(lines)


def calculate_metrics(
    equity_curve: list[EquityPoint],
    fills: list[Fill],
    initial_capital: float,
    trading_days_per_year: int = 252,
    risk_free_rate: float = 0.0,
    timeframe: str = "1d",
    trades: list[CompletedTrade] | None = None,
) -> PerformanceMetrics:
    """
    Backtest sonucundan performans metrikleri hesapla.

    Args:
        equity_curve: Equity curve noktaları
        fills: Dolum listesi
        initial_capital: Başlangıç sermayesi
        trading_days_per_year: Yıllık işlem günü
            (geriye dönük uyumluluk, timeframe kullanılır)
        risk_free_rate: Risksiz faiz oranı (yıllık)
        timeframe: Veri zaman dilimi ("1d", "1h", vb.)
        trades: CompletedTrade listesi (varsa)

    Returns:
        PerformanceMetrics: Tüm metrikler
    """
    metrics = PerformanceMetrics(
        initial_capital=initial_capital,
        timeframe=timeframe,
    )

    if not equity_curve:
        return metrics

    # Annualization factor
    ann_factor = _get_annualization_factor(timeframe)

    # --- Equity serisini hazırla ---
    equities = pd.Series(
        [ep.total_equity for ep in equity_curve]
    )
    timestamps = pd.Series(
        [ep.timestamp for ep in equity_curve]
    )
    final_equity = equities.iloc[-1]
    metrics.final_equity = final_equity

    # --- Getiri ---
    metrics.total_return_pct = (
        (final_equity / initial_capital - 1) * 100
    )
    metrics.net_return_pct = metrics.total_return_pct

    # CAGR — gerçek tarih farkından hesapla
    if len(timestamps) > 1:
        start_ts = pd.Timestamp(timestamps.iloc[0])
        end_ts = pd.Timestamp(timestamps.iloc[-1])
        delta_days = (end_ts - start_ts).days

        if delta_days > 0 and final_equity > 0:
            years = delta_days / 365.25
            metrics.cagr_pct = (
                (
                    (final_equity / initial_capital)
                    ** (1 / years)
                    - 1
                )
                * 100
            )
            metrics.annualized_return_pct = (
                metrics.cagr_pct
            )
        elif delta_days == 0:
            metrics.warnings.append(
                "Başlangıç ve bitiş tarihi aynı, "
                "CAGR hesaplanamadı."
            )

    # --- Bar getiriler ---
    bar_returns = equities.pct_change().dropna()

    if len(bar_returns) > 1:
        # Volatilite (yıllık)
        metrics.volatility_annual = (
            bar_returns.std() * np.sqrt(ann_factor) * 100
        )

        # Sharpe Ratio (timeframe-aware)
        bar_rf = risk_free_rate / ann_factor
        excess_returns = bar_returns - bar_rf
        if bar_returns.std() > 0:
            metrics.sharpe_ratio = (
                excess_returns.mean()
                / bar_returns.std()
            ) * np.sqrt(ann_factor)

        # Sortino Ratio (sadece negatif getirilerle)
        downside_returns = bar_returns[bar_returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            if downside_std > 0:
                metrics.sortino_ratio = (
                    excess_returns.mean() / downside_std
                ) * np.sqrt(ann_factor)

    # --- Drawdown ---
    metrics.max_drawdown_pct = max(
        (ep.drawdown_pct for ep in equity_curve),
        default=0.0,
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
        metrics.max_drawdown_duration_days = (
            max_dd_duration
        )

    # Calmar Ratio
    if metrics.max_drawdown_pct > 0:
        metrics.calmar_ratio = (
            metrics.cagr_pct / metrics.max_drawdown_pct
        )

    # --- Trade İstatistikleri ---
    # CompletedTrade varsa onlardan hesapla (doğru yol)
    if trades:
        _calculate_trade_stats_from_trades(
            metrics, trades, fills, final_equity,
            initial_capital,
        )
    else:
        # Geriye dönük uyumluluk: fill eşleştirmesi
        _calculate_trade_stats_from_fills(
            metrics, fills, final_equity, initial_capital,
        )

    # --- Exposure ---
    if equity_curve:
        exposed_bars = sum(
            1
            for ep in equity_curve
            if ep.position_value > 0
        )
        metrics.exposure_pct = (
            exposed_bars / len(equity_curve) * 100
        )

    return metrics


def _calculate_trade_stats_from_trades(
    metrics: PerformanceMetrics,
    trades: list[CompletedTrade],
    fills: list[Fill],
    final_equity: float,
    initial_capital: float,
) -> None:
    """CompletedTrade nesnelerinden trade istatistikleri."""
    metrics.total_trades = len(trades)
    metrics.trade_count = len(trades)

    if not trades:
        return

    winners = [t for t in trades if t.is_winner]
    losers = [t for t in trades if not t.is_winner]

    metrics.winning_trades = len(winners)
    metrics.losing_trades = len(losers)
    metrics.win_rate = (
        len(winners) / len(trades) * 100
    )

    if winners:
        win_pnls = [t.net_pnl for t in winners]
        metrics.avg_win = sum(win_pnls) / len(win_pnls)
        metrics.largest_win = max(win_pnls)
    if losers:
        loss_pnls = [t.net_pnl for t in losers]
        metrics.avg_loss = sum(loss_pnls) / len(loss_pnls)
        metrics.largest_loss = min(loss_pnls)

    # Profit Factor
    gross_profit = (
        sum(t.net_pnl for t in winners) if winners else 0
    )
    gross_loss = (
        abs(sum(t.net_pnl for t in losers))
        if losers
        else 0
    )
    if gross_loss > 0:
        metrics.profit_factor = gross_profit / gross_loss

    # Maliyet metrikleri
    metrics.total_commission = sum(
        t.total_commission for t in trades
    )
    metrics.total_slippage_cost = sum(
        t.total_slippage_cost for t in trades
    )

    # Slippage dahil olmayan fill'lerden de ekle
    if fills:
        total_fill_commission = sum(
            f.commission for f in fills
        )
        total_fill_slippage = sum(
            f.slippage_cost for f in fills
        )
        # Trade'lerden hesaplanan değeri override etme,
        # fill'lerden gelen daha doğru olabilir
        metrics.total_commission = total_fill_commission
        metrics.total_slippage_cost = total_fill_slippage

    # Gross return (komisyon + slippage öncesi)
    total_costs = (
        metrics.total_commission
        + metrics.total_slippage_cost
    )
    metrics.gross_return_pct = (
        (final_equity + total_costs)
        / initial_capital
        - 1
    ) * 100

    # Holding period
    holding_bars = [t.holding_bars for t in trades]
    if holding_bars:
        metrics.avg_holding_bars = (
            sum(holding_bars) / len(holding_bars)
        )


def _calculate_trade_stats_from_fills(
    metrics: PerformanceMetrics,
    fills: list[Fill],
    final_equity: float,
    initial_capital: float,
) -> None:
    """Geriye dönük uyumluluk: Fill eşleştirmesiyle."""
    buy_fills = [
        f for f in fills if f.order.side == OrderSide.BUY
    ]
    sell_fills = [
        f
        for f in fills
        if f.order.side == OrderSide.SELL
    ]

    trade_pnls: list[float] = []
    for sell in sell_fills:
        matching_buys = [
            b
            for b in buy_fills
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
            metrics.profit_factor = (
                gross_profit / gross_loss
            )

        # Maliyet metrikleri
        total_commission = sum(
            f.commission for f in fills
        )
        total_slippage = sum(
            f.slippage_cost for f in fills
        )
        metrics.total_commission = total_commission
        metrics.total_slippage_cost = total_slippage
        metrics.gross_return_pct = (
            (final_equity + total_commission)
            / initial_capital
            - 1
        ) * 100

    # Holding Period
    if buy_fills and sell_fills:
        holding_bars: list[int] = []
        for sell in sell_fills:
            matching_buys = [
                b
                for b in buy_fills
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

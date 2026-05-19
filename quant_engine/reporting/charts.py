"""
Quant Engine — Grafik Üretici (Plotly)

Equity curve, drawdown, aylık heatmap ve trade marker grafikleri.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quant_engine.backtest.domain import EquityPoint, Fill, OrderSide


def create_equity_chart(
    equity_curve: list[EquityPoint],
    title: str = "Equity Curve",
    initial_capital: float = 100_000,
) -> go.Figure:
    """Equity curve grafiği."""
    dates = [ep.timestamp for ep in equity_curve]
    equity = [ep.total_equity for ep in equity_curve]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=equity, name="Toplam Equity",
        line={"color": "#2ecc71", "width": 2.5},
        fill="tozeroy", fillcolor="rgba(46,204,113,0.1)",
    ))
    fig.add_hline(
        y=initial_capital, line_dash="dash",
        line_color="rgba(255,255,255,0.3)",
        annotation_text=f"Başlangıç: ₺{initial_capital:,.0f}",
    )
    fig.update_layout(
        title=title, xaxis_title="Tarih", yaxis_title="Değer (₺)",
        template="plotly_dark", hovermode="x unified", height=400,
        margin={"l": 60, "r": 30, "t": 50, "b": 40},
        yaxis={"tickformat": ",.0f"},
    )
    return fig


def create_drawdown_chart(
    equity_curve: list[EquityPoint],
    title: str = "Drawdown",
) -> go.Figure:
    """Drawdown grafiği."""
    dates = [ep.timestamp for ep in equity_curve]
    dd_pct = [-ep.drawdown_pct for ep in equity_curve]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=dd_pct, name="Drawdown",
        line={"color": "#e74c3c", "width": 1.5},
        fill="tozeroy", fillcolor="rgba(231,76,60,0.3)",
    ))
    fig.update_layout(
        title=title, xaxis_title="Tarih", yaxis_title="Drawdown (%)",
        template="plotly_dark", hovermode="x unified", height=250,
        margin={"l": 60, "r": 30, "t": 50, "b": 40},
        yaxis={"ticksuffix": "%"},
    )
    return fig


def create_monthly_heatmap(
    equity_curve: list[EquityPoint],
    title: str = "Aylık Getiriler (%)",
) -> go.Figure:
    """Aylık getiri heatmap'i."""
    dates = [ep.timestamp for ep in equity_curve]
    equity = [ep.total_equity for ep in equity_curve]
    df = pd.DataFrame({"date": dates, "equity": equity})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    monthly = df["equity"].resample("ME").last()
    monthly_returns = monthly.pct_change() * 100

    pivot_data: dict[int, dict[int, float]] = {}
    for dt_idx, ret in monthly_returns.items():
        yr, mo = dt_idx.year, dt_idx.month
        pivot_data.setdefault(yr, {})[mo] = ret

    if not pivot_data:
        return go.Figure(layout={"title": title, "template": "plotly_dark"})

    years = sorted(pivot_data.keys())
    month_names = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                    "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

    z, text = [], []
    for yr in years:
        row, trow = [], []
        for mo in range(1, 13):
            val = pivot_data.get(yr, {}).get(mo)
            if val is not None and not pd.isna(val):
                row.append(val)
                trow.append(f"{val:+.1f}%")
            else:
                row.append(None)
                trow.append("")
        z.append(row)
        text.append(trow)

    fig = go.Figure(data=go.Heatmap(
        z=z, x=month_names, y=[str(y) for y in years],
        text=text, texttemplate="%{text}",
        colorscale=[[0, "#e74c3c"], [0.5, "#2c3e50"], [1, "#2ecc71"]],
        zmid=0,
    ))
    fig.update_layout(
        title=title, template="plotly_dark",
        height=max(200, len(years) * 60 + 100),
        margin={"l": 60, "r": 30, "t": 50, "b": 40},
    )
    return fig


def create_trade_chart(
    data: pd.DataFrame,
    fills: list[Fill],
    equity_curve: list[EquityPoint],
    symbol: str = "UNKNOWN",
) -> go.Figure:
    """Fiyat + al/sat işaretleri + equity curve (2 panel)."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08, row_heights=[0.6, 0.4],
        subplot_titles=[f"{symbol} — Fiyat", "Equity Curve"],
    )

    dates = pd.to_datetime(data["date"])
    fig.add_trace(go.Scatter(
        x=dates, y=data["close"], name="Kapanış",
        line={"color": "#3498db", "width": 1.5},
    ), row=1, col=1)

    buy_fills = [f for f in fills if f.order.side == OrderSide.BUY]
    if buy_fills:
        fig.add_trace(go.Scatter(
            x=[f.fill_timestamp for f in buy_fills],
            y=[f.fill_price for f in buy_fills],
            mode="markers", name="AL",
            marker={"symbol": "triangle-up", "size": 12, "color": "#2ecc71"},
        ), row=1, col=1)

    sell_fills = [f for f in fills if f.order.side == OrderSide.SELL]
    if sell_fills:
        fig.add_trace(go.Scatter(
            x=[f.fill_timestamp for f in sell_fills],
            y=[f.fill_price for f in sell_fills],
            mode="markers", name="SAT",
            marker={"symbol": "triangle-down", "size": 12, "color": "#e74c3c"},
        ), row=1, col=1)

    eq_dates = [ep.timestamp for ep in equity_curve]
    eq_values = [ep.total_equity for ep in equity_curve]
    fig.add_trace(go.Scatter(
        x=eq_dates, y=eq_values, name="Equity",
        line={"color": "#2ecc71", "width": 2},
        fill="tozeroy", fillcolor="rgba(46,204,113,0.1)",
    ), row=2, col=1)

    fig.update_layout(
        title=f"{symbol} — Backtest Raporu",
        template="plotly_dark", hovermode="x unified",
        height=700, showlegend=True,
        margin={"l": 60, "r": 30, "t": 60, "b": 40},
    )
    fig.update_yaxes(title_text="Fiyat (₺)", row=1, col=1)
    fig.update_yaxes(title_text="Equity (₺)", row=2, col=1, tickformat=",.0f")
    return fig

"""
Quant Engine — Profesyonel Streamlit Araştırma Terminali

Özellikler:
    1. Dashboard: Portföy özeti, veri durumu
    2. Backtest Lab: Strateji çalıştırma, metrikler, equity curve
    3. Parametre Optimizasyonu: Grid Search + walk-forward
    4. Veri Yönetimi: Storage durumu, doğrulama

Internet yoksa demo modda çalışır (yapay veri).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Proje kökünü ekle
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from quant_engine.backtest.engine import (  # noqa: E402
    BacktestConfig,
    BacktestEngine,
)
from quant_engine.backtest.metrics import (  # noqa: E402
    calculate_metrics,
)
from quant_engine.strategy.base import BaseStrategy  # noqa: E402
from quant_engine.strategy.examples.buy_and_hold import BuyAndHold  # noqa: E402
from quant_engine.strategy.examples.rsi_reversion import RsiReversion  # noqa: E402
from quant_engine.strategy.examples.sma_crossover import SmaCrossover  # noqa: E402

# ─── Yapay Veri ────────────────────────────────────────

def generate_synthetic_data(
    n_bars: int = 500,
    seed: int = 42,
    symbol: str = "SYNTH",
) -> pd.DataFrame:
    """Yapay OHLCV verisi."""
    rng = np.random.default_rng(seed)
    trend = np.linspace(0, 0.3, n_bars)
    noise = rng.standard_normal(n_bars) * 0.02
    returns = trend / n_bars + noise
    prices = 100.0 * np.exp(np.cumsum(returns))
    close = prices
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (
        1 + rng.uniform(0, 0.02, n_bars)
    )
    low = np.minimum(open_, close) * (
        1 - rng.uniform(0, 0.02, n_bars)
    )
    volume = rng.integers(500_000, 5_000_000, n_bars)
    dates = pd.bdate_range(
        "2022-01-03", periods=n_bars, freq="B"
    )
    return pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "symbol": [symbol] * n_bars,
    })


# ─── Strateji Fabrikası ───────────────────────────────

STRATEGY_MAP: dict[str, type[BaseStrategy]] = {
    "SMA Crossover": SmaCrossover,
    "RSI Reversion": RsiReversion,
    "Buy & Hold": BuyAndHold,
}


# ─── Yardımcı UI Fonksiyonları ────────────────────────

def render_metric_card(
    label: str,
    value: float,
    is_percentage: bool = False,
    condition: str = "",
):
    """Metrik kartı."""
    if is_percentage:
        display = f"{value:.2f}%"
    elif isinstance(value, int):
        display = f"{value:,}"
    else:
        display = f"{value:.2f}"

    if condition == "profit":
        color = "#00ff88" if value > 0 else "#ff4444"
    elif condition == "loss":
        color = "#ff4444"
    else:
        color = "#00d4ff"

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.05);
            border: 1px solid {color}33;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        ">
            <div style="
                color: #888;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">{label}</div>
            <div style="
                color: {color};
                font-size: 28px;
                font-weight: 700;
                margin-top: 4px;
            ">{display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_equity_chart(result, strategy_name: str):
    """Equity curve çiz."""
    if not HAS_PLOTLY:
        st.warning("Plotly kurulu değil.")
        return

    eq_data = [
        {
            "date": ep.timestamp,
            "equity": ep.total_equity,
            "cash": ep.cash,
            "position": ep.position_value,
            "drawdown": ep.drawdown_pct,
        }
        for ep in result.equity_curve
    ]
    df = pd.DataFrame(eq_data)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=(
            f"Equity Curve — {strategy_name}",
            "Drawdown (%)",
        ),
    )

    # Equity line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["equity"],
            mode="lines",
            name="Toplam Sermaye",
            line=dict(color="#00ff88", width=2),
            fill="tozeroy",
            fillcolor="rgba(0,255,136,0.1)",
        ),
        row=1, col=1,
    )

    # Drawdown
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=-df["drawdown"],
            mode="lines",
            name="Drawdown",
            line=dict(color="#ff4444", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(255,68,68,0.15)",
        ),
        row=2, col=1,
    )

    fig.update_layout(
        template="plotly_dark",
        height=550,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=60, r=20, t=40, b=40),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

    st.plotly_chart(fig, use_container_width=True)


def render_trade_table(result):
    """Trade tablosu göster."""
    if not result.trades:
        if result.fills:
            st.info(
                f"Toplam {len(result.fills)} fill "
                f"(tamamlanmış trade yok — "
                f"pozisyon açık olabilir)."
            )
        else:
            st.info("İşlem yapılmadı.")
        return

    rows = []
    for t in result.trades:
        rows.append({
            "Giriş": (
                t.entry_date.strftime("%Y-%m-%d")
                if t.entry_date else "—"
            ),
            "Çıkış": (
                t.exit_date.strftime("%Y-%m-%d")
                if t.exit_date else "—"
            ),
            "Adet": t.quantity,
            "Giriş₺": f"{t.entry_price:.2f}",
            "Çıkış₺": f"{t.exit_price:.2f}",
            "PnL₺": f"{t.net_pnl:+,.0f}",
            "PnL%": f"{t.pnl_pct:+.2f}%",
            "Bar": t.holding_bars,
            "Sonuç": "✅" if t.is_winner else "❌",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ─── Sayfalar ─────────────────────────────────────────

def page_backtest_lab():
    """Backtest Lab sayfası."""
    st.markdown(
        "## 🧪 Backtest Lab",
    )

    # Sidebar - Parametreler
    with st.sidebar:
        st.markdown("### ⚙️ Parametreler")

        # Sermaye
        capital = st.number_input(
            "Başlangıç Sermayesi (₺)",
            min_value=10_000,
            max_value=10_000_000,
            value=100_000,
            step=10_000,
        )

        # Maliyet
        commission = st.slider(
            "Komisyon (%)",
            0.0, 1.0, 0.1, 0.01,
        ) / 100
        slippage = st.slider(
            "Slippage (bps)",
            0, 50, 5,
        )
        max_pos = st.slider(
            "Maks. Pozisyon (%)",
            10, 100, 95,
        ) / 100

        st.markdown("---")

        # Strateji
        strategy_name = st.selectbox(
            "Strateji",
            list(STRATEGY_MAP.keys()),
        )

        # Strateji parametreleri
        st.markdown("#### 📊 Strateji Ayarları")
        params = {}

        if strategy_name == "SMA Crossover":
            params["fast_period"] = st.slider(
                "Hızlı SMA", 3, 50, 10,
            )
            params["slow_period"] = st.slider(
                "Yavaş SMA", 10, 100, 30,
            )
        elif strategy_name == "RSI Reversion":
            params["rsi_period"] = st.slider(
                "RSI Periyodu", 5, 30, 14,
            )
            params["oversold"] = st.slider(
                "Aşırı Satım", 10, 40, 30,
            )
            params["overbought"] = st.slider(
                "Aşırı Alım", 60, 90, 70,
            )

        st.markdown("---")

        # Veri
        bar_count = st.slider(
            "Bar Sayısı", 100, 2000, 500,
        )
        data_seed = st.number_input(
            "Veri Seed", 1, 9999, 42,
        )

        run_btn = st.button(
            "🚀 Backtest Çalıştır",
            type="primary",
            use_container_width=True,
        )

    # Ana alan
    if run_btn:
        # Config
        config = BacktestConfig(
            initial_capital=float(capital),
            commission_rate=commission,
            slippage_bps=slippage,
            max_position_pct=max_pos,
        )

        # Strateji oluştur
        strategy_cls = STRATEGY_MAP[strategy_name]
        try:
            strategy = strategy_cls(params=params or None)
        except ValueError as e:
            st.error(f"Parametre hatası: {e}")
            return

        # Validasyon
        errors = strategy.validate_params()
        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
            return

        # Veri
        data = generate_synthetic_data(
            bar_count, data_seed,
        )

        # Backtest çalıştır
        with st.spinner("Backtest çalışıyor..."):
            strategy.prepare(data)
            engine = BacktestEngine(config)
            result = engine.run(
                data,
                strategy.as_signal_func(),
                symbol="SYNTH",
            )
            metrics = calculate_metrics(
                result.equity_curve,
                result.fills,
                config.initial_capital,
                trades=result.trades,
            )

        # Uyarılar
        if result.warnings:
            for w in result.warnings:
                st.warning(w)

        # Metrik kartları
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            cond = (
                "profit"
                if metrics.total_return_pct > 0
                else "loss"
            )
            render_metric_card(
                "Net Getiri",
                metrics.total_return_pct,
                True, cond,
            )
        with k2:
            render_metric_card(
                "Max Drawdown",
                metrics.max_drawdown_pct,
                True, "loss",
            )
        with k3:
            render_metric_card(
                "Sharpe", metrics.sharpe_ratio,
            )
        with k4:
            render_metric_card(
                "CAGR",
                metrics.cagr_pct,
                True,
                "profit" if metrics.cagr_pct > 0 else "loss",
            )

        k5, k6, k7, k8 = st.columns(4)
        with k5:
            render_metric_card(
                "Sortino", metrics.sortino_ratio,
            )
        with k6:
            render_metric_card(
                "Win Rate",
                metrics.win_rate,
                True,
            )
        with k7:
            render_metric_card(
                "Profit Factor",
                metrics.profit_factor,
            )
        with k8:
            render_metric_card(
                "Toplam Trade",
                float(metrics.total_trades),
            )

        st.markdown("---")

        # Equity Curve
        render_equity_chart(result, strategy_name)

        # Trade tablosu
        st.markdown("### 📋 İşlem Geçmişi")
        render_trade_table(result)

        # Maliyet özeti
        st.markdown("### 💰 Maliyet Analizi")
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card(
                "Komisyon",
                metrics.total_commission,
            )
        with c2:
            render_metric_card(
                "Slippage",
                metrics.total_slippage_cost,
            )
        with c3:
            render_metric_card(
                "Brüt Getiri",
                metrics.gross_return_pct,
                True,
            )

        # Detaylı metrikler
        with st.expander("📊 Tüm Metrikler"):
            st.text(metrics.summary())

    else:
        st.info(
            "Soldaki menüden parametreleri "
            "seçip 'Backtest Çalıştır' butonuna basın."
        )


def page_optimizer():
    """Parametre Optimizasyonu sayfası."""
    st.markdown("## 🔍 Parametre Optimizasyonu")

    with st.sidebar:
        st.markdown("### ⚙️ Optimizer Ayarları")

        strategy_name = st.selectbox(
            "Strateji",
            ["SMA Crossover", "RSI Reversion"],
            key="opt_strategy",
        )

        capital = st.number_input(
            "Sermaye (₺)",
            10_000, 10_000_000, 100_000, 10_000,
            key="opt_capital",
        )

        bar_count = st.slider(
            "Bar Sayısı",
            200, 2000, 500,
            key="opt_bars",
        )

        st.markdown("---")
        st.markdown("#### 📊 Parametre Aralıkları")

        if strategy_name == "SMA Crossover":
            fast_min = st.number_input(
                "Fast SMA Min", 3, 20, 5,
            )
            fast_max = st.number_input(
                "Fast SMA Max", 10, 50, 20,
            )
            fast_step = st.number_input(
                "Fast SMA Step", 1, 10, 5,
            )
            slow_min = st.number_input(
                "Slow SMA Min", 15, 50, 20,
            )
            slow_max = st.number_input(
                "Slow SMA Max", 30, 200, 60,
            )
            slow_step = st.number_input(
                "Slow SMA Step", 5, 20, 10,
            )
        else:
            rsi_min = st.number_input(
                "RSI Min", 5, 20, 7,
            )
            rsi_max = st.number_input(
                "RSI Max", 10, 30, 21,
            )
            rsi_step = st.number_input(
                "RSI Step", 1, 5, 7,
            )

        ranking = st.selectbox(
            "Sıralama Metriği",
            [
                "sharpe_ratio",
                "total_return_pct",
                "sortino_ratio",
                "calmar_ratio",
            ],
        )

        run_opt = st.button(
            "🔍 Optimizasyonu Başlat",
            type="primary",
            use_container_width=True,
        )

    if run_opt:
        from quant_engine.research.optimizer import (
            GridSearchOptimizer,
        )

        config = BacktestConfig(
            initial_capital=float(capital),
            commission_rate=0.001,
            slippage_bps=5,
            max_position_pct=0.95,
        )

        data = generate_synthetic_data(
            bar_count, 42,
        )

        strategy_cls = STRATEGY_MAP[strategy_name]

        # Parametre grid oluştur
        if strategy_name == "SMA Crossover":
            param_grid = {
                "fast_period": list(range(
                    int(fast_min),
                    int(fast_max) + 1,
                    int(fast_step),
                )),
                "slow_period": list(range(
                    int(slow_min),
                    int(slow_max) + 1,
                    int(slow_step),
                )),
            }
        else:
            param_grid = {
                "rsi_period": list(range(
                    int(rsi_min),
                    int(rsi_max) + 1,
                    int(rsi_step),
                )),
                "oversold": [25, 30, 35],
                "overbought": [65, 70, 75],
            }

        total = 1
        for v in param_grid.values():
            total *= len(v)

        st.info(f"📊 Toplam {total} kombinasyon test edilecek...")

        progress = st.progress(0)

        def update_progress(completed, total_n):
            progress.progress(completed / total_n)

        optimizer = GridSearchOptimizer(
            config, data, "SYNTH",
        )
        optimizer.set_progress_callback(update_progress)

        with st.spinner("Optimizasyon çalışıyor..."):
            opt_result = optimizer.run(
                strategy_cls,
                param_grid,
                ranking,
            )

        progress.progress(1.0)

        # Uyarılar
        for w in opt_result.warnings:
            st.warning(w)

        # Sonuç tablosu
        st.markdown("### 🏆 Sonuçlar")
        df = opt_result.to_dataframe()
        if not df.empty:
            st.dataframe(
                df.style.highlight_max(
                    subset=[ranking],
                    color="rgba(0,255,136,0.3)",
                ),
                use_container_width=True,
                hide_index=True,
            )

            # En iyi sonuç
            if opt_result.best_run:
                best = opt_result.best_run
                st.markdown("### 🥇 En İyi Parametreler")
                st.json(best.params)

                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    render_metric_card(
                        "Sharpe",
                        best.metrics.sharpe_ratio,
                    )
                with k2:
                    cond = (
                        "profit"
                        if best.metrics.total_return_pct > 0
                        else "loss"
                    )
                    render_metric_card(
                        "Getiri",
                        best.metrics.total_return_pct,
                        True, cond,
                    )
                with k3:
                    render_metric_card(
                        "Max DD",
                        best.metrics.max_drawdown_pct,
                        True, "loss",
                    )
                with k4:
                    render_metric_card(
                        "Win Rate",
                        best.metrics.win_rate,
                        True,
                    )

        st.info(
            f"⏱️ Toplam süre: "
            f"{opt_result.total_duration_seconds:.1f}s | "
            f"Tamamlanan: "
            f"{opt_result.completed_combinations}"
            f"/{opt_result.total_combinations}"
        )
    else:
        st.info(
            "Soldaki menüden parametre aralıklarını "
            "belirleyip 'Optimizasyonu Başlat' butonuna basın."
        )


def page_data_station():
    """Veri Yönetimi sayfası."""
    st.markdown("## 📦 Veri İstasyonu")

    st.markdown(
        """
        ### Veri Durumu
        Henüz gerçek veri yüklenmedi. Backtest Lab
        sayfasında yapay veri ile çalışabilirsiniz.

        **Gelecek özellikler:**
        - Yahoo Finance'den veri çekme
        - Parquet depolama yönetimi
        - Veri kalite kontrolleri
        - Çoklu sembol takibi
        """
    )

    # Demo veri istatistikleri
    st.markdown("### 📊 Demo Veri")
    data = generate_synthetic_data(500)

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card(
            "Bar Sayısı", float(len(data)),
        )
    with col2:
        render_metric_card(
            "İlk Fiyat", float(data["close"].iloc[0]),
        )
    with col3:
        render_metric_card(
            "Son Fiyat", float(data["close"].iloc[-1]),
        )

    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data["date"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="SYNTH",
        ))
        fig.update_layout(
            template="plotly_dark",
            height=400,
            title="Demo Yapay Veri (SYNTH)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ─── Ana Uygulama ────────────────────────────────────

def main():
    """Ana Streamlit uygulaması."""
    if not HAS_STREAMLIT:
        print("Streamlit kurulu değil!")
        print("pip install streamlit")
        return

    st.set_page_config(
        page_title="Quant Engine Terminal",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS
    st.markdown(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?'
            'family=Inter:wght@400;600;700&display=swap'
        );
        .stApp {
            font-family: 'Inter', sans-serif;
        }
        .stApp > header {
            background: transparent;
        }
        section[data-testid="stSidebar"] {
            background: rgba(10,10,20,0.95);
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
        ">
            <span style="font-size: 32px;">📈</span>
            <div>
                <h1 style="
                    margin:0;
                    font-size: 24px;
                    color: #00ff88;
                ">Quant Engine Terminal</h1>
                <p style="
                    margin:0;
                    color: #666;
                    font-size: 12px;
                ">BIST Algorithmic Research Terminal v0.2</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigasyon
    page = st.sidebar.radio(
        "Sayfa",
        [
            "🧪 Backtest Lab",
            "🔍 Optimizer",
            "📦 Veri İstasyonu",
        ],
        label_visibility="collapsed",
    )

    if page == "🧪 Backtest Lab":
        page_backtest_lab()
    elif page == "🔍 Optimizer":
        page_optimizer()
    elif page == "📦 Veri İstasyonu":
        page_data_station()


if __name__ == "__main__":
    main()

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Proje ana dizinini path'e ekliyoruz ki quant_engine paketini içeri aktarabilelim
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from quant_engine.backtest.engine import BacktestConfig, BacktestEngine
from quant_engine.backtest.metrics import calculate_metrics
from quant_engine.strategy.examples.buy_and_hold import BuyAndHold
from quant_engine.strategy.examples.sma_crossover import SmaCrossover
from quant_engine.strategy.examples.rsi_reversion import RsiReversion
from demo import generate_synthetic_data

st.set_page_config(
    page_title="Quant Engine Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Arayüzü daha profesyonel göstermek için özel CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #252540;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 3px solid #333366;
    }
    .metric-title {
        font-size: 14px;
        color: #a0a0b0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .profit { color: #00ff88; border-left: 3px solid #00ff88; }
    .loss { color: #ff3366; border-left: 3px solid #ff3366; }
</style>
""", unsafe_allow_html=True)

def render_metric_card(title, value, is_percentage=False, is_currency=False, condition="neutral"):
    color_class = ""
    if condition == "profit":
        color_class = "profit"
    elif condition == "loss":
        color_class = "loss"
    
    formatted_val = f"{value:,.2f}" if isinstance(value, (int, float)) else value
    if is_percentage:
        formatted_val += "%"
    elif is_currency:
        formatted_val = f"₺{formatted_val}"
        
    st.markdown(f"""
    <div class="metric-card {color_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value {color_class}">{formatted_val}</div>
    </div>
    """, unsafe_allow_html=True)

def view_dashboard():
    st.header("Dashboard & Veri İstasyonu")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Aktif Sembol", "1 (SYNTH)")
    with col2:
        render_metric_card("Toplam Bar", "500", condition="profit")
    with col3:
        render_metric_card("Sistem Durumu", "Çevrimdışı", condition="loss")
    with col4:
        render_metric_card("Motor Versiyonu", "v0.1.0")

    st.subheader("Veri Sağlık Kontrolü")
    data = {"Sembol": ["SYNTH", "THYAO", "GARAN"], 
            "Durum": ["✅ Güncel", "❌ Veri Çekilemedi", "❌ Veri Çekilemedi"],
            "Eksik Gün": [0, "-", "-"],
            "Son Tarih": ["2023-12-01", "-", "-"]}
    st.dataframe(pd.DataFrame(data), use_container_width=True)

def view_matrix_scanner():
    st.header("Matrix Tarama Paneli")
    st.write("Sistemdeki tüm sembollerin anlık sinyal ve metrik özeti.")
    
    # Gerçek veri entegre edilene kadar sistemin konseptini gösteren mock veri
    data = {
        "Sembol": ["THYAO", "GARAN", "AKBNK", "SYNTH"],
        "Günlük Trend": ["🟢 Yukarı", "🟢 Yukarı", "⚪ Nötr", "🟢 Yukarı"],
        "RSI": [65.2, 58.1, 45.0, 72.5],
        "Son Sinyal": ["AL", "AL", "BEKLE", "SAT"],
        "Backtest Getirisi": ["+24.5%", "+18.2%", "+5.4%", "+12.8%"],
        "Sharpe": [1.2, 0.9, 0.4, 1.8]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def view_strategy_builder():
    st.header("Strateji Kurucu ve Laboratuvar")
    
    col_sidebar, col_main = st.columns([1, 3])
    
    with col_sidebar:
        st.subheader("Parametreler")
        strategy_name = st.selectbox("Strateji Tipi", ["RSI Reversion", "SMA Crossover", "Buy & Hold"])
        
        st.markdown("---")
        if strategy_name == "RSI Reversion":
            rsi_period = st.slider("RSI Periyodu", 5, 30, 14)
            oversold = st.slider("Aşırı Satım", 10, 40, 30)
            overbought = st.slider("Aşırı Alım", 60, 90, 70)
            strategy = RsiReversion(params={"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought})
        elif strategy_name == "SMA Crossover":
            fast_ma = st.slider("Hızlı SMA", 5, 50, 10)
            slow_ma = st.slider("Yavaş SMA", 20, 200, 30)
            strategy = SmaCrossover(params={"fast_period": fast_ma, "slow_period": slow_ma})
        else:
            strategy = BuyAndHold()

        st.markdown("---")
        capital = st.number_input("Başlangıç Sermayesi (₺)", value=100000, step=10000)
        commission = st.number_input("Komisyon Oranı (%)", value=0.1, step=0.01) / 100.0
        slippage = st.number_input("Slippage (BPS)", value=5, step=1)
        
        run_btn = st.button("🚀 Backtest Çalıştır", type="primary", use_container_width=True)

    with col_main:
        if run_btn:
            with st.spinner("Backtest çalıştırılıyor..."):
                # İnternet sorunu nedeniyle her zaman sentetik veri (yapay veri) kullanıyoruz
                df = generate_synthetic_data(n_bars=500, symbol="SYNTH")
                
                config = BacktestConfig(
                    initial_capital=capital,
                    commission_rate=commission,
                    slippage_bps=int(slippage),
                    max_position_pct=0.95,
                    warm_up_bars=0
                )
                
                engine = BacktestEngine(config)
                result = engine.run(df, strategy.as_signal_func(), symbol="SYNTH")
                metrics = calculate_metrics(result.equity_curve, result.fills, capital)
                
                # KPI Kartları
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    render_metric_card("Net Getiri", metrics.total_return_pct, is_percentage=True, condition="profit" if metrics.total_return_pct > 0 else "loss")
                with k2:
                    render_metric_card("Max Drawdown", metrics.max_drawdown_pct, is_percentage=True, condition="loss")
                with k3:
                    render_metric_card("Sharpe", metrics.sharpe_ratio)
                with k4:
                    render_metric_card("Win Rate", metrics.win_rate, is_percentage=True)
                
                # Grafikler
                try:
                    import plotly.graph_objects as go
                    
                    st.subheader("Sermaye Eğrisi (Equity Curve)")
                    
                    eq_df = pd.DataFrame([{
                        "date": eq.timestamp, 
                        "equity": eq.total_equity
                    } for eq in result.equity_curve])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=eq_df["date"], y=eq_df["equity"], mode="lines", name="Sermaye", line=dict(color="#00ff88")))
                    fig.update_layout(
                        template="plotly_dark", 
                        paper_bgcolor="#1a1a2e", 
                        plot_bgcolor="#1a1a2e",
                        margin=dict(l=0, r=0, t=30, b=0)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                except ImportError:
                    st.warning("Grafiklerin çizilmesi için 'plotly' kütüphanesi eksik. İnternet erişimi sağlandığında kurulmalıdır.")
                
                # İşlem Tablosu
                st.subheader("Trade Inspector (İşlem Denetleyicisi)")
                if result.fills:
                    fills_data = []
                    for f in result.fills[::-1]:
                        fills_data.append({
                            "Tarih": f.fill_timestamp.strftime("%Y-%m-%d"),
                            "Yön": "AL" if f.order.side.value == "buy" else "SAT",
                            "Fiyat": f"₺{f.fill_price:.2f}",
                            "Adet": f.fill_quantity,
                            "Komisyon": f"₺{f.commission:.2f}"
                        })
                    st.dataframe(pd.DataFrame(fills_data), use_container_width=True)
                else:
                    st.info("Bu strateji hiç işlem yapmadı.")
        else:
            st.info("Lütfen soldaki menüden parametreleri seçip 'Backtest Çalıştır' butonuna basın.")

def main():
    st.sidebar.title("Navigasyon")
    page = st.sidebar.radio("Sayfalar", ["Dashboard", "Matrix Tarayıcı", "Strateji Kurucu"])

    if page == "Dashboard":
        view_dashboard()
    elif page == "Matrix Tarayıcı":
        view_matrix_scanner()
    elif page == "Strateji Kurucu":
        view_strategy_builder()

if __name__ == "__main__":
    main()

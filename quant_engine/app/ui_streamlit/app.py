"""
Quant Engine - gerçek veri odaklı araştırma ve backtest terminali.

Bu Streamlit uygulaması kullanıcıya açık hiçbir akışta gerçek dışı OHLCV üretmez.
Veri sağlayıcıdan veri gelmezse grafik, matris ve strateji çıktıları bekleme/hata
durumunda kalır.
"""

from __future__ import annotations

import datetime as dt
import html as html_lib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

# Proje kökünü ekle. Streamlit dosyayı doğrudan çalıştırdığı için gerekli.
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

from quant_engine.backtest.engine import BacktestConfig, BacktestEngine  # noqa: E402
from quant_engine.backtest.metrics import calculate_metrics  # noqa: E402
from quant_engine.core.protocols import BarRequest, Market, Timeframe  # noqa: E402
from quant_engine.data.providers.binance_provider import BinanceProvider  # noqa: E402
from quant_engine.data.providers.yfinance_provider import YFinanceProvider  # noqa: E402
from quant_engine.data_pipeline.data_validator import DataValidator  # noqa: E402
from quant_engine.strategy.base import BaseStrategy  # noqa: E402
from quant_engine.strategy.blueprint_engine import (  # noqa: E402
    BLUEPRINT_INDICATOR_OPTIONS,
    DEFAULT_BLUEPRINT_INDICATORS,
    build_strategy_blueprint,
)
from quant_engine.strategy.decision_engine import DecisionReport, analyze_market_data  # noqa: E402
from quant_engine.strategy.examples.bollinger_reversion import BollingerReversion  # noqa: E402
from quant_engine.strategy.examples.buy_and_hold import BuyAndHold  # noqa: E402
from quant_engine.strategy.examples.rsi_reversion import RsiReversion  # noqa: E402
from quant_engine.strategy.examples.sma_crossover import SmaCrossover  # noqa: E402
from quant_engine.strategy.indicators import bollinger_bands, rsi, sma  # noqa: E402
from quant_engine.strategy.persistence import StrategyStore  # noqa: E402
from quant_engine.strategy.registry import get_registry  # noqa: E402
from quant_engine.workspace.json_store import WorkspaceJsonStore  # noqa: E402
from quant_engine.workspace.manager import (  # noqa: E402
    BIST30_INSTRUMENTS,
    BIST_WIDE_INSTRUMENTS,
    COMMODITY_INSTRUMENTS,
    CRYPTO_INSTRUMENTS,
    FOREX_INSTRUMENTS,
    WorkspaceRequest,
    build_workspace_config,
    resolve_workspace,
    workspace_warning_text,
)

if HAS_STREAMLIT:
    cache_data = st.cache_data(show_spinner=False)
else:

    def cache_data(func):
        return func


BIST30_SYMBOLS: dict[str, str] = BIST30_INSTRUMENTS
BIST_SYMBOLS: dict[str, str] = BIST_WIDE_INSTRUMENTS
STOCKANALYSIS_BIST_URLS = (
    "https://stockanalysis.com/list/borsa-istanbul/",
    "https://stockanalysis.com/list/borsa-istanbul/?page=2",
)

STRATEGY_LABELS: dict[str, str] = {
    "sma_crossover": "SMA Kesişimi",
    "rsi_reversion": "RSI Dönüşü",
    "bollinger_reversion": "Bollinger Dönüşü",
    "buy_and_hold": "Al ve Tut",
}


def _registered_strategy_map() -> dict[str, type[BaseStrategy]]:
    """Registry'den UI'ın kullandığı Türkçe strateji listesini üret."""
    registry = get_registry()
    fallback = {
        "SMA Kesişimi": SmaCrossover,
        "RSI Dönüşü": RsiReversion,
        "Bollinger Dönüşü": BollingerReversion,
        "Al ve Tut": BuyAndHold,
    }
    mapped: dict[str, type[BaseStrategy]] = {}
    for item in registry.list_strategies():
        internal_name = item["name"]
        label = STRATEGY_LABELS.get(internal_name, internal_name.replace("_", " ").title())
        mapped[label] = registry.get_class(internal_name)
    return mapped or fallback


STRATEGY_MAP: dict[str, type[BaseStrategy]] = _registered_strategy_map()

TIMEFRAME_OPTIONS = {
    "Günlük": Timeframe.D1,
    "Haftalık": Timeframe.W1,
    "Aylık": Timeframe.MO1,
}

DASHBOARD_ASSETS: tuple[dict[str, Any], ...] = (
    {"label": "BIST 100", "symbol": "XU100", "market": Market.BIST, "precision": 2},
    {"label": "USD/TRY", "symbol": "USDTRY", "market": Market.FOREX, "precision": 4},
    {"label": "XAU/USD", "symbol": "XAUUSD", "market": Market.COMMODITY, "precision": 2},
    {"label": "BTC/USDT", "symbol": "BTCUSDT", "market": Market.CRYPTO, "precision": 2},
    {"label": "ETH/USDT", "symbol": "ETHUSDT", "market": Market.CRYPTO, "precision": 2},
)

OPEN_WINDOWS_KEY = "terminal:open_windows"

RANKING_OPTIONS = {
    "Sharpe oranı": "sharpe_ratio",
    "Toplam getiri": "total_return_pct",
    "Sortino oranı": "sortino_ratio",
    "Calmar oranı": "calmar_ratio",
}

STRATEGY_DETAILS = {
    "SMA Kesişimi": {
        "code": "sma_crossover",
        "indicator": "SMA",
        "summary": "Hızlı ortalama yavaş ortalamayı yukarı kestiğinde alır.",
        "buy_rule": "Hızlı SMA, yavaş SMA'yı yukarı keser ve pozisyon yoktur.",
        "sell_rule": "Hızlı SMA, yavaş SMA'yı aşağı keser ve açık pozisyon vardır.",
        "risk": "Yatay piyasada sık al-sat yapıp maliyet üretebilir.",
    },
    "RSI Dönüşü": {
        "code": "rsi_reversion",
        "indicator": "RSI",
        "summary": "Aşırı satış bölgesinden tepki bekler, aşırı alımda çıkar.",
        "buy_rule": "RSI aşırı satış eşiğinin altına iner ve pozisyon yoktur.",
        "sell_rule": "RSI aşırı alım eşiğinin üstüne çıkar ve açık pozisyon vardır.",
        "risk": "Güçlü düşüş trendinde erken alım sinyali verebilir.",
    },
    "Bollinger Dönüşü": {
        "code": "bollinger_reversion",
        "indicator": "Bollinger Bands",
        "summary": "Alt bandın dışına taşan fiyatın ortalamaya dönmesini bekler.",
        "buy_rule": "Kapanış alt bandın altına iner ve pozisyon yoktur.",
        "sell_rule": "Kapanış seçilen çıkış bandına, orta veya üst banda, ulaşır.",
        "risk": "Sert trend düşüşlerinde alt bant boyunca erken alım yapabilir.",
    },
    "Al ve Tut": {
        "code": "buy_and_hold",
        "indicator": "Benchmark",
        "summary": "İlk fırsatta alır ve dönem sonuna kadar pozisyonu taşır.",
        "buy_rule": "İlk barda pozisyon yoksa alır.",
        "sell_rule": "Satış sinyali üretmez; açık pozisyonu dönem sonuna taşır.",
        "risk": "Düşüş dönemlerinde koruma mekanizması yoktur.",
    },
}


@dataclass(frozen=True)
class ChartOptions:
    show_sma: bool = True
    show_bollinger: bool = True
    show_volume: bool = True
    show_equity: bool = True
    show_drawdown: bool = True
    show_trade_lines: bool = True
    log_price: bool = False
    range_label: str = "Tümü"


@dataclass
class TradeOverlay:
    markers: pd.DataFrame
    segments: pd.DataFrame
    open_segments: pd.DataFrame


def _symbol_label(symbol: str) -> str:
    return f"{symbol} - {BIST_SYMBOLS.get(symbol, symbol)}"


def _selected_symbol(label: str) -> str:
    return label.split(" - ", 1)[0]


def _parse_bist_catalog_html(raw_html: str) -> dict[str, str]:
    """StockAnalysis BIST liste HTML'inden sembol/şirket eşleşmesini çıkar."""
    pattern = re.compile(
        r'<td class="sym[^"]*">.*?'
        r'<a href="/quote/ist/([A-Z0-9]+)/">.*?</a>.*?</td>.*?'
        r'<td class="slw[^"]*">(.*?)</td>',
        flags=re.DOTALL,
    )
    rows: dict[str, str] = {}
    for symbol, raw_name in pattern.findall(raw_html):
        clean_name = re.sub(r"<.*?>", "", raw_name)
        rows[symbol.upper()] = html_lib.unescape(clean_name).strip()
    return rows


@cache_data
def load_online_bist_catalog() -> tuple[dict[str, str], list[str]]:
    """Güncel BIST sembol kataloğunu çevrimiçi listeden dene, olmazsa yerel listeye dön."""
    rows: dict[str, str] = {}
    warnings: list[str] = []
    for url in STOCKANALYSIS_BIST_URLS:
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=8) as response:
                page = response.read().decode("utf-8", "ignore")
        except (OSError, URLError) as exc:
            warnings.append(f"BIST katalog sayfası okunamadı: {url} ({exc})")
            continue
        page_rows = _parse_bist_catalog_html(page)
        if not page_rows:
            warnings.append(f"BIST katalog sayfası boş döndü: {url}")
            continue
        rows.update(page_rows)

    if not rows:
        warnings.append("Çevrimiçi BIST kataloğu alınamadı; yerel geniş liste kullanıldı.")
        return BIST_SYMBOLS, warnings

    merged = dict(sorted({**BIST_SYMBOLS, **rows}.items()))
    return merged, warnings


def _format_number(value: Any, percentage: bool = False) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        suffix = "%" if percentage else ""
        return f"{float(value):,.2f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)


def _provider_for_market(market: Market, timeout: float = 15):
    """Piyasaya göre gerçek veri provider'ını seç."""
    if market == Market.CRYPTO:
        return BinanceProvider(timeout=timeout)
    return YFinanceProvider(timeout=timeout)


def load_symbol_data(
    symbol: str,
    start_date: dt.date,
    timeframe: Timeframe,
    market: Market = Market.BIST,
) -> tuple[pd.DataFrame, list[str]]:
    """UI için yalnızca gerçek veri yükle; başarısızlıkta boş veri döndür."""
    provider = _provider_for_market(market, timeout=15)
    result = provider.fetch_bars(
        BarRequest(
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            start=start_date,
            end=dt.date.today(),
        )
    )
    if not result.success:
        errors = result.errors or ["Geçerli piyasa verisi bulunamadı."]
        return pd.DataFrame(), errors
    return result.data, result.warnings


def build_strategy(
    strategy_name: str,
    params: dict[str, Any],
) -> BaseStrategy:
    strategy_cls = STRATEGY_MAP[strategy_name]
    return strategy_cls(params=params or None)


def run_backtest(
    data: pd.DataFrame,
    symbol: str,
    strategy_name: str,
    params: dict[str, Any],
    config: BacktestConfig,
    timeframe: str = "1d",
):
    strategy = build_strategy(strategy_name, params)
    errors = strategy.validate_params()
    if errors:
        raise ValueError("; ".join(errors))

    strategy.prepare(data)
    engine = BacktestEngine(config)
    result = engine.run(data, strategy.as_signal_func(), symbol=symbol)
    metrics = calculate_metrics(
        result.equity_curve,
        result.fills,
        config.initial_capital,
        timeframe=timeframe,
        trades=result.trades,
    )
    return strategy, result, metrics


def render_metric_card(
    label: str,
    value: Any,
    percentage: bool = False,
    tone: str = "neutral",
):
    color = {
        "good": "#16c784",
        "bad": "#ea3943",
        "warn": "#f0b90b",
        "neutral": "#8ab4ff",
    }.get(tone, "#8ab4ff")
    display = _format_number(value, percentage)
    st.markdown(
        f"""
        <div class="qe-metric" style="border-color:{color}55;">
            <div class="qe-metric-label">{label}</div>
            <div class="qe-metric-value" style="color:{color};">{display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_strip(metrics, result):
    values = [
        (
            "Net",
            metrics.total_return_pct,
            True,
            "good" if metrics.total_return_pct >= 0 else "bad",
        ),
        ("Maks DD", metrics.max_drawdown_pct, True, "bad"),
        (
            "Sharpe",
            metrics.sharpe_ratio,
            False,
            "good" if metrics.sharpe_ratio > 1 else "warn",
        ),
        ("Yıllık", metrics.cagr_pct, True, "good" if metrics.cagr_pct >= 0 else "bad"),
        ("Sortino", metrics.sortino_ratio, False, "neutral"),
        ("Kazanma", metrics.win_rate, True, "neutral"),
        ("Trade", metrics.total_trades, False, "neutral"),
        (
            "Pozisyon",
            "Var" if result.has_open_position else "Yok",
            False,
            "warn" if result.has_open_position else "good",
        ),
    ]
    for start in range(0, len(values), 4):
        cols = st.columns(4)
        for col, item in zip(cols, values[start : start + 4]):
            label, value, percentage, tone = item
            with col:
                render_metric_card(label, value, percentage, tone)


@cache_data
def load_market_snapshot(
    symbol: str,
    market_value: str,
    start_date_iso: str,
    timeframe_value: str,
) -> dict[str, Any]:
    """Dashboard kartları için gerçek piyasa verisinden son durum üret."""
    market = Market(market_value)
    timeframe = Timeframe(timeframe_value)
    data, warnings = load_symbol_data(
        symbol=symbol,
        start_date=dt.date.fromisoformat(start_date_iso),
        timeframe=timeframe,
        market=market,
    )
    if data.empty:
        return {
            "symbol": symbol,
            "market": market.value,
            "status": "Veri yok",
            "warnings": warnings,
            "rows": 0,
        }
    latest = data.iloc[-1]
    previous_close = float(data["close"].iloc[-2]) if len(data) > 1 else float(latest["close"])
    last_close = float(latest["close"])
    daily_pct = ((last_close / previous_close) - 1) * 100 if previous_close else 0.0
    return {
        "symbol": symbol,
        "market": market.value,
        "status": "Hazır",
        "last": last_close,
        "daily_pct": daily_pct,
        "high": float(latest["high"]),
        "low": float(latest["low"]),
        "volume": float(latest.get("volume", 0.0)),
        "last_date": _format_date(latest["date"]),
        "rows": len(data),
        "source": "binance" if market == Market.CRYPTO else "yfinance",
        "warnings": warnings,
    }


def _window_key(symbol: str, market: Market, timeframe: Timeframe = Timeframe.D1) -> str:
    return f"{market.value}:{symbol.upper()}:{timeframe.value}"


def _open_terminal_window(label: str, symbol: str, market: Market) -> None:
    windows = list(st.session_state.get(OPEN_WINDOWS_KEY, []))
    key = _window_key(symbol, market)
    if not any(item["key"] == key for item in windows):
        windows.append(
            {
                "key": key,
                "label": label,
                "symbol": symbol.upper(),
                "market": market.value,
                "timeframe": Timeframe.D1.value,
            }
        )
    st.session_state[OPEN_WINDOWS_KEY] = windows


def _close_terminal_window(key: str) -> None:
    st.session_state[OPEN_WINDOWS_KEY] = [
        item for item in st.session_state.get(OPEN_WINDOWS_KEY, []) if item["key"] != key
    ]


def render_snapshot_card(asset: dict[str, Any], snapshot: dict[str, Any]) -> None:
    label = asset["label"]
    if snapshot.get("status") != "Hazır":
        render_metric_card(label, "Veri yok", tone="warn")
        return
    tone = "good" if snapshot["daily_pct"] >= 0 else "bad"
    render_metric_card(
        label,
        f"{snapshot['last']:.{asset['precision']}f} ({snapshot['daily_pct']:+.2f}%)",
        tone=tone,
    )
    st.caption(f"{snapshot['last_date']} | {snapshot['source']} | {snapshot['rows']} bar")


def render_window_chart(data: pd.DataFrame, symbol: str, precision: int) -> None:
    """Bağımsız terminal penceresi için gerçek veriden kompakt grafik çiz."""
    if data.empty:
        st.warning("Bu pencere gerçek veri bekliyor; sahte mum çizilmiyor.")
        return
    latest = data.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Son", round(float(latest["close"]), precision))
    with c2:
        daily_pct = float(data["close"].pct_change().iloc[-1] * 100) if len(data) > 1 else 0.0
        render_metric_card("Gün %", daily_pct, True, "good" if daily_pct >= 0 else "bad")
    with c3:
        render_metric_card("Yüksek", round(float(latest["high"]), precision), tone="good")
    with c4:
        render_metric_card("Düşük", round(float(latest["low"]), precision), tone="bad")

    if not HAS_PLOTLY:
        st.dataframe(data.tail(40), width="stretch", hide_index=True)
        return
    chart_df = data.tail(260).copy()
    chart_df["sma20"] = sma(chart_df["close"], 20)
    chart_df["sma50"] = sma(chart_df["close"], 50)
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=chart_df["date"],
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name="Mum",
            increasing_line_color="#16c784",
            decreasing_line_color="#ea3943",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["sma20"],
            mode="lines",
            name="SMA 20",
            line=dict(color="#f0b90b", width=1.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["sma50"],
            mode="lines",
            name="SMA 50",
            line=dict(color="#8ab4ff", width=1.2),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=460,
        margin=dict(l=20, r=20, t=30, b=20),
        title=f"{symbol} Bağımsız Analiz Penceresi",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
    )
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})


def page_dashboard():
    st.markdown("## Ana Gösterge Paneli")
    st.caption(
        "Piyasa özeti ve sembole özel bağımsız analiz pencereleri yalnızca gerçek "
        "provider verisi geldikten sonra çizilir."
    )
    start_iso = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    cols = st.columns(len(DASHBOARD_ASSETS))
    for col, asset in zip(cols, DASHBOARD_ASSETS):
        with col:
            snapshot = load_market_snapshot(
                asset["symbol"],
                asset["market"].value,
                start_iso,
                Timeframe.D1.value,
            )
            render_snapshot_card(asset, snapshot)
            for warning in snapshot.get("warnings", [])[:1]:
                st.caption(warning)

    st.markdown("### Pencere Aç")
    c1, c2, c3, c4 = st.columns([0.28, 0.28, 0.28, 0.16])
    with c1:
        market_label = st.selectbox(
            "Piyasa",
            ["BIST 100", "Forex", "Emtia", "Kripto"],
            key="dashboard_market",
        )
    with c2:
        if market_label == "Forex":
            options = list(FOREX_INSTRUMENTS)
        elif market_label == "Emtia":
            options = list(COMMODITY_INSTRUMENTS)
        elif market_label == "Kripto":
            options = list(CRYPTO_INSTRUMENTS)
        else:
            options = list(BIST_SYMBOLS)
        symbol = st.selectbox("Sembol", options, key=f"dashboard_symbol_{market_label}")
    with c3:
        custom_symbol = st.text_input(
            "Özel sembol",
            value="",
            help="Örn: THYAO, SASA, USDTRY, XAUUSD, BTCUSDT.",
        )
        if custom_symbol.strip():
            symbol = custom_symbol.strip().upper().replace(".IS", "")
    with c4:
        st.write("")
        st.write("")
        if st.button("Aç", type="primary", width="stretch"):
            resolution = resolve_workspace(
                WorkspaceRequest(symbol_id=symbol, market_type=market_label, timeframe_label="1G")
            )
            if resolution.valid:
                _open_terminal_window(
                    resolution.instrument.full_name,
                    resolution.instrument.symbol_code,
                    resolution.instrument.market,
                )
            else:
                st.warning(workspace_warning_text(resolution))

    windows = st.session_state.get(OPEN_WINDOWS_KEY, [])
    if not windows:
        st.info("Bir sembol seçip pencere açınca burada bağımsız grafik sekmesi oluşur.")
        return

    st.markdown("### Açık Pencereler")
    tabs = st.tabs([item["symbol"] for item in windows])
    for tab, item in zip(tabs, list(windows)):
        with tab:
            market = Market(item["market"])
            resolution = resolve_workspace(
                WorkspaceRequest(
                    symbol_id=item["symbol"],
                    market_type=market.value,
                    timeframe_label="1G",
                )
            )
            left, right = st.columns([0.84, 0.16])
            with left:
                st.markdown(f"#### {item['symbol']} - {item['label']}")
            with right:
                if st.button("Kapat", key=f"close_{item['key']}", width="stretch"):
                    _close_terminal_window(item["key"])
                    st.rerun()
            data, warnings = load_symbol_data(
                item["symbol"],
                start_date=dt.date.today() - dt.timedelta(days=365),
                timeframe=Timeframe.D1,
                market=market,
            )
            for warning in warnings[:3]:
                st.warning(warning)
            precision = resolution.instrument.precision if resolution.valid else 2
            render_window_chart(data, item["symbol"], precision)


def render_decision_report(report: DecisionReport):
    """Gerçek veri karar motoru çıktısını standart formatta göster."""
    tone = {
        "AL": "good",
        "SAT": "bad",
        "BEKLE": "warn",
        "VERİ YETERSİZ": "neutral",
    }.get(report.decision, "neutral")
    c1, c2 = st.columns([0.25, 0.75])
    with c1:
        render_metric_card("Karar", report.decision, tone=tone)
    with c2:
        render_metric_card("Strateji Türü", report.strategy_type, tone=tone)

    if report.decision == "VERİ YETERSİZ":
        st.warning(report.data_status)
    elif report.decision == "AL":
        st.success(report.data_status)
    elif report.decision == "SAT":
        st.error(report.data_status)
    else:
        st.info(report.data_status)

    st.code(report.to_log_text(), language="text")

    if report.snapshot is None:
        return

    s = report.snapshot
    st.markdown("#### Kullanılan Son Gerçek Veri")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Sembol": s.symbol,
                    "Zaman": s.latest_time,
                    "Periyot": s.timeframe,
                    "Fiyat": s.current_price,
                    "Hacim": s.volume,
                    "EMA 200": s.ema200,
                    "BB Alt": s.bb_lower,
                    "BB Orta": s.bb_middle,
                    "BB Üst": s.bb_upper,
                    "RSI 14": s.rsi14,
                    "Önceki RSI": s.prev_rsi14,
                }
            ]
        ),
        width="stretch",
        hide_index=True,
    )


def render_strategy_blueprint_json(blueprint: dict[str, Any]):
    """Frontend'in parse edebileceği katı JSON çıktısını göster."""
    st.code(
        json.dumps(blueprint, ensure_ascii=False, indent=2),
        language="json",
    )


def _format_date(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _format_signed_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "Açık"
    return f"{float(value):+.2f}%"


def build_trade_overlay(result, data: pd.DataFrame) -> TradeOverlay:
    """Grafik için marker, trade bağlantısı ve açık pozisyon verisini hazırla."""
    completed_by_entry = {
        trade.entry_bar_index: (trade_id, trade)
        for trade_id, trade in enumerate(result.trades, start=1)
    }
    completed_by_exit = {
        trade.exit_bar_index: (trade_id, trade)
        for trade_id, trade in enumerate(result.trades, start=1)
    }
    completed_entry_bars = set(completed_by_entry)
    marker_rows: list[dict[str, Any]] = []
    open_rows: list[dict[str, Any]] = []
    open_trade_id = len(result.trades) + 1

    for fill in result.fills:
        side_value = fill.order.side.value
        is_buy = side_value == "buy"
        trade_ref = (
            completed_by_entry.get(fill.bar_index)
            if is_buy
            else completed_by_exit.get(fill.bar_index)
        )
        if trade_ref:
            trade_id, trade = trade_ref
        else:
            trade_id, trade = open_trade_id, None
            if is_buy:
                open_trade_id += 1

        pnl_pct = trade.pnl_pct if trade else None
        pnl = trade.net_pnl if trade else None
        side_label = "AL" if is_buy else "SAT"
        marker_rows.append(
            {
                "trade_id": trade_id,
                "side": side_label,
                "date": fill.fill_timestamp,
                "price": fill.fill_price,
                "quantity": fill.fill_quantity,
                "signal_date": fill.order.signal_timestamp,
                "fill_date": fill.fill_timestamp,
                "commission": fill.commission,
                "slippage_cost": fill.slippage_cost,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "pnl_text": _format_signed_pct(pnl_pct),
                "label": (
                    f"{side_label} #{trade_id}"
                    if is_buy
                    else f"{side_label} #{trade_id}<br>{_format_signed_pct(pnl_pct)}"
                ),
            }
        )

        if is_buy and fill.bar_index not in completed_entry_bars:
            last_bar = data.iloc[-1]
            open_rows.append(
                {
                    "trade_id": trade_id,
                    "entry_date": fill.fill_timestamp,
                    "entry_price": fill.fill_price,
                    "last_date": last_bar["date"],
                    "last_price": float(last_bar["close"]),
                    "quantity": fill.fill_quantity,
                }
            )

    segment_rows = [
        {
            "trade_id": trade_id,
            "entry_date": trade.entry_date,
            "entry_price": trade.entry_price,
            "exit_date": trade.exit_date,
            "exit_price": trade.exit_price,
            "net_pnl": trade.net_pnl,
            "pnl_pct": trade.pnl_pct,
            "color": "#16c784" if trade.net_pnl >= 0 else "#ea3943",
            "label": f"#{trade_id} {_format_signed_pct(trade.pnl_pct)}",
        }
        for trade_id, trade in enumerate(result.trades, start=1)
    ]
    return TradeOverlay(
        markers=pd.DataFrame(marker_rows),
        segments=pd.DataFrame(segment_rows),
        open_segments=pd.DataFrame(open_rows),
    )


def _date_window_start(data: pd.DataFrame, label: str) -> pd.Timestamp | None:
    if label == "Tümü" or data.empty:
        return None
    last_date = pd.Timestamp(data["date"].iloc[-1])
    if label == "1 Ay":
        return last_date - pd.DateOffset(months=1)
    if label == "3 Ay":
        return last_date - pd.DateOffset(months=3)
    if label == "6 Ay":
        return last_date - pd.DateOffset(months=6)
    if label == "1 Yıl":
        return last_date - pd.DateOffset(years=1)
    if label == "Yıl başı":
        return pd.Timestamp(year=last_date.year, month=1, day=1)
    return None


def _selected_trade_id_from_event(event: Any) -> int | None:
    if isinstance(event, dict):
        points = event.get("selection", {}).get("points")
    else:
        points = getattr(getattr(event, "selection", None), "points", None)
    if not points:
        return None
    customdata = points[0].get("customdata") if isinstance(points[0], dict) else None
    if not customdata:
        return None
    try:
        return int(customdata[0])
    except (TypeError, ValueError):
        return None


def render_market_chart(
    data: pd.DataFrame,
    result,
    symbol: str,
    options: ChartOptions,
) -> int | None:
    """TradingView hissine yakın, ama backtest odaklı ana grafik."""
    if not HAS_PLOTLY:
        st.warning("Grafik için Plotly kurulu değil.")
        return None

    chart_df = data.copy()
    chart_df["sma20"] = sma(chart_df["close"], 20)
    chart_df["sma50"] = sma(chart_df["close"], 50)
    bb_upper, bb_middle, bb_lower = bollinger_bands(chart_df["close"], 20, 2.0)
    chart_df["bb_upper"] = bb_upper
    chart_df["bb_middle"] = bb_middle
    chart_df["bb_lower"] = bb_lower
    overlay = build_trade_overlay(result, chart_df)
    equity_df = pd.DataFrame(
        [
            {
                "date": ep.timestamp,
                "equity": ep.total_equity,
                "drawdown": -ep.drawdown_pct,
            }
            for ep in result.equity_curve
        ]
    )

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.52, 0.13, 0.2, 0.15],
        subplot_titles=(
            f"{symbol} Fiyat, SMA ve İşlemler",
            "Hacim",
            "Sermaye Eğrisi",
            "Düşüş (Drawdown)",
        ),
    )
    fig.add_trace(
        go.Candlestick(
            x=chart_df["date"],
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name="Mum",
            increasing_line_color="#16c784",
            decreasing_line_color="#ea3943",
        ),
        row=1,
        col=1,
    )

    if options.show_sma:
        fig.add_trace(
            go.Scatter(
                x=chart_df["date"],
                y=chart_df["sma20"],
                mode="lines",
                name="SMA 20",
                line=dict(color="#f0b90b", width=1.4),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=chart_df["date"],
                y=chart_df["sma50"],
                mode="lines",
                name="SMA 50",
                line=dict(color="#8ab4ff", width=1.4),
            ),
            row=1,
            col=1,
        )

    if options.show_bollinger:
        fig.add_trace(
            go.Scatter(
                x=chart_df["date"],
                y=chart_df["bb_upper"],
                mode="lines",
                name="BB Üst",
                line=dict(color="rgba(240,185,11,0.75)", width=1, dash="dot"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=chart_df["date"],
                y=chart_df["bb_lower"],
                mode="lines",
                name="BB Alt",
                fill="tonexty",
                fillcolor="rgba(240,185,11,0.08)",
                line=dict(color="rgba(240,185,11,0.75)", width=1, dash="dot"),
            ),
            row=1,
            col=1,
        )

    if options.show_trade_lines and not overlay.segments.empty:
        for idx, segment in overlay.segments.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[segment["entry_date"], segment["exit_date"]],
                    y=[segment["entry_price"], segment["exit_price"]],
                    mode="lines",
                    name="Trade bağlantısı",
                    legendgroup="trade_segments",
                    showlegend=idx == 0,
                    line=dict(color=segment["color"], width=2.2),
                    hovertemplate=(
                        f"Trade #{segment['trade_id']}<br>"
                        f"Net PnL: {segment['net_pnl']:+.2f}<br>"
                        f"PnL: {segment['pnl_pct']:+.2f}%<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

    if options.show_trade_lines and not overlay.open_segments.empty:
        for idx, segment in overlay.open_segments.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[segment["entry_date"], segment["last_date"]],
                    y=[segment["entry_price"], segment["last_price"]],
                    mode="lines",
                    name="Açık pozisyon",
                    legendgroup="open_positions",
                    showlegend=idx == 0,
                    line=dict(color="#f0b90b", width=2, dash="dot"),
                    hovertemplate=(
                        f"Açık trade #{segment['trade_id']}<br>"
                        "Son bara kadar taşınıyor<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

    if not overlay.markers.empty:
        custom_cols = [
            "trade_id",
            "side",
            "signal_date",
            "fill_date",
            "quantity",
            "commission",
            "slippage_cost",
            "pnl",
            "pnl_text",
        ]
        marker_specs = [
            ("AL", "#16c784", "triangle-up", "top center"),
            ("SAT", "#ea3943", "triangle-down", "bottom center"),
        ]
        for side, color, symbol_name, text_position in marker_specs:
            side_df = overlay.markers[overlay.markers["side"] == side]
            if side_df.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=side_df["date"],
                    y=side_df["price"],
                    mode="markers+text",
                    name=side,
                    marker=dict(
                        symbol=symbol_name,
                        size=18,
                        color=color,
                        line=dict(width=2, color="#f8fafc"),
                    ),
                    text=side_df["label"],
                    textposition=text_position,
                    textfont=dict(size=11, color=color),
                    customdata=side_df[custom_cols].to_numpy(),
                    hovertemplate=(
                        "<b>%{customdata[1]} #%{customdata[0]}</b><br>"
                        "Sinyal: %{customdata[2]|%Y-%m-%d}<br>"
                        "İşlem: %{customdata[3]|%Y-%m-%d}<br>"
                        "Fiyat: %{y:.2f}<br>"
                        "Adet: %{customdata[4]}<br>"
                        "Komisyon: %{customdata[5]:.2f}<br>"
                        "Kayma: %{customdata[6]:.2f}<br>"
                        "Sonuç: %{customdata[8]}<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

    volume_color = np.where(
        chart_df["close"] >= chart_df["open"],
        "rgba(22,199,132,0.55)",
        "rgba(234,57,67,0.55)",
    )
    if options.show_volume:
        fig.add_trace(
            go.Bar(
                x=chart_df["date"],
                y=chart_df["volume"],
                name="Hacim",
                marker_color=volume_color,
            ),
            row=2,
            col=1,
        )
    if options.show_equity:
        fig.add_trace(
            go.Scatter(
                x=equity_df["date"],
                y=equity_df["equity"],
                mode="lines",
                name="Sermaye",
                line=dict(color="#16c784", width=2),
            ),
            row=3,
            col=1,
        )
    if options.show_drawdown:
        fig.add_trace(
            go.Scatter(
                x=equity_df["date"],
                y=equity_df["drawdown"],
                mode="lines",
                name="Düşüş",
                fill="tozeroy",
                line=dict(color="#ea3943", width=1.5),
            ),
            row=4,
            col=1,
        )

    range_start = _date_window_start(chart_df, options.range_label)
    if range_start is not None:
        fig.update_xaxes(
            range=[range_start, pd.Timestamp(chart_df["date"].iloc[-1])],
            row=1,
            col=1,
        )

    fig.update_layout(
        template="plotly_dark",
        height=820,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=20, t=70, b=30),
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(family="Inter, Arial", size=12),
        hovermode="x unified",
        dragmode="pan",
        xaxis=dict(
            rangeslider=dict(visible=False),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1A", step="month", stepmode="backward"),
                    dict(count=3, label="3A", step="month", stepmode="backward"),
                    dict(count=6, label="6A", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="Tümü"),
                ],
                bgcolor="#151b24",
                activecolor="#16c784",
                font=dict(color="#e6edf3"),
            ),
        ),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(type="log" if options.log_price else "linear", row=1, col=1)
    event = st.plotly_chart(
        fig,
        width="stretch",
        key=f"{symbol}_trade_chart",
        on_select="rerun",
        selection_mode="points",
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )
    return _selected_trade_id_from_event(event)


def render_trade_table(result):
    if not result.trades:
        if result.fills:
            st.info(
                f"{len(result.fills)} emir gerçekleşti; kapanmış trade yok. "
                "Pozisyon hâlâ açık olabilir."
            )
        else:
            st.info("Bu koşulda işlem oluşmadı.")
        return

    rows = []
    for trade in result.trades:
        rows.append(
            {
                "Giriş Tarihi": trade.entry_date.strftime("%Y-%m-%d"),
                "Çıkış Tarihi": trade.exit_date.strftime("%Y-%m-%d"),
                "Adet": trade.quantity,
                "Giriş": round(trade.entry_price, 2),
                "Çıkış": round(trade.exit_price, 2),
                "Brüt PnL": round(trade.gross_pnl, 2),
                "Net PnL": round(trade.net_pnl, 2),
                "PnL %": round(trade.pnl_pct, 2),
                "Komisyon": round(trade.total_commission, 2),
                "Kayma": round(trade.total_slippage_cost, 2),
                "Bar": trade.holding_bars,
                "Sonuç": "Kazanç" if trade.is_winner else "Kayıp",
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_strategy_panel(
    strategy_name: str,
    strategy: BaseStrategy,
    params: dict[str, Any],
):
    detail = STRATEGY_DETAILS.get(strategy_name, {})
    st.markdown("### Strateji Kartı")
    st.markdown(
        f"""
        <div class="qe-info-panel">
            <div class="qe-panel-title">{strategy_name}</div>
            <div class="qe-panel-muted">{detail.get("summary", strategy.description)}</div>
            <div class="qe-rule"><b>Kod:</b> {detail.get("code", strategy.name)}</div>
            <div class="qe-rule"><b>İndikatör:</b> {detail.get("indicator", "-")}</div>
            <div class="qe-rule"><b>Warm-up:</b> {strategy.warm_up_bars} bar</div>
            <div class="qe-rule"><b>AL:</b> {detail.get("buy_rule", "-")}</div>
            <div class="qe-rule"><b>SAT:</b> {detail.get("sell_rule", "-")}</div>
            <div class="qe-risk">{detail.get("risk", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if params:
        st.caption("Aktif parametreler")
        st.json(params, expanded=False)


def render_trade_detail_panel(result, selected_trade_id: int | None):
    st.markdown("### İşlem Detayı")
    if not result.trades:
        st.info("Kapanmış trade yok. Grafikte açık pozisyon varsa sarı kesikli çizgiyle görünür.")
        return

    trade_id = selected_trade_id or 1
    trade_id = max(1, min(trade_id, len(result.trades)))
    trade = result.trades[trade_id - 1]
    tone = "good" if trade.net_pnl >= 0 else "bad"
    render_metric_card(f"Trade #{trade_id} Net PnL", trade.net_pnl, tone=tone)
    c1, c2 = st.columns(2)
    with c1:
        render_metric_card("PnL %", trade.pnl_pct, True, tone)
    with c2:
        render_metric_card("Bar", trade.holding_bars)
    st.markdown(
        f"""
        <div class="qe-info-panel">
            <div class="qe-rule">
                <b>Giriş:</b> {_format_date(trade.entry_date)} @ {trade.entry_price:.2f}
            </div>
            <div class="qe-rule">
                <b>Çıkış:</b> {_format_date(trade.exit_date)} @ {trade.exit_price:.2f}
            </div>
            <div class="qe-rule"><b>Adet:</b> {trade.quantity}</div>
            <div class="qe-rule"><b>Komisyon:</b> {trade.total_commission:.2f}</div>
            <div class="qe-rule"><b>Kayma:</b> {trade.total_slippage_cost:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_strategy_comparison(
    data: pd.DataFrame,
    symbol: str,
    config: BacktestConfig,
    timeframe: str,
    selected_strategy_name: str,
    selected_params: dict[str, Any],
) -> pd.DataFrame:
    rows = []
    for strategy_name in STRATEGY_MAP:
        params = selected_params if strategy_name == selected_strategy_name else {}
        try:
            _, result, metrics = run_backtest(
                data,
                symbol,
                strategy_name,
                params,
                config,
                timeframe=timeframe,
            )
        except ValueError as exc:
            rows.append(
                {
                    "Strateji": strategy_name,
                    "Durum": f"Hatalı: {exc}",
                }
            )
            continue
        rows.append(
            {
                "Strateji": strategy_name,
                "Net Getiri %": round(metrics.total_return_pct, 2),
                "Maks. Düşüş %": round(metrics.max_drawdown_pct, 2),
                "Sharpe": round(metrics.sharpe_ratio, 2),
                "Kazanma %": round(metrics.win_rate, 2),
                "Trade": metrics.total_trades,
                "Açık Poz.": "Var" if result.has_open_position else "Yok",
                "Durum": (
                    "Düşük örnek"
                    if 0 < metrics.total_trades < 5
                    else "İzlenebilir"
                ),
            }
        )
    df = pd.DataFrame(rows)
    if "Net Getiri %" in df:
        df = df.sort_values("Net Getiri %", ascending=False, na_position="last")
    return df


def render_strategy_comparison(df: pd.DataFrame):
    if df.empty:
        st.info("Karşılaştırılacak strateji sonucu yok.")
        return

    def color_return(value: float) -> str:
        if pd.isna(value):
            return ""
        if value >= 0:
            return "background-color: rgba(22,199,132,0.18)"
        return "background-color: rgba(234,57,67,0.18)"

    styled = df.style.map(color_return, subset=["Net Getiri %"]).format(
        {
            "Net Getiri %": "{:+.2f}",
            "Maks. Düşüş %": "{:.2f}",
            "Sharpe": "{:.2f}",
            "Kazanma %": "{:.2f}",
        }
    )
    st.dataframe(styled, width="stretch", hide_index=True)


def _simulated_trade_volume(result) -> float:
    return float(sum(fill.fill_price * fill.fill_quantity for fill in result.fills))


def _trade_pct_stats(result) -> tuple[float, float, float]:
    if not result.trades:
        return 0.0, 0.0, 0.0
    pct_values = [trade.pnl_pct for trade in result.trades]
    return max(pct_values), min(pct_values), float(np.mean(pct_values))


@cache_data
def build_strategy_leaderboard(
    symbols: tuple[str, ...],
    start_date_iso: str,
    timeframe_value: str,
    strategy_names: tuple[str, ...],
    initial_capital: float,
    commission_rate: float,
    slippage_bps: int,
    max_position_pct: float,
) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    warnings: list[str] = []
    config = BacktestConfig(
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        slippage_bps=slippage_bps,
        max_position_pct=max_position_pct,
    )
    requested = tuple(strategy_names) or tuple(STRATEGY_MAP)
    timeframe = Timeframe(timeframe_value)
    start_date = dt.date.fromisoformat(start_date_iso)
    provider = YFinanceProvider(timeout=12)
    validator = DataValidator(min_rows=60)

    for symbol in symbols:
        company = BIST_SYMBOLS.get(symbol, symbol)
        fetch = provider.fetch_bars(
            BarRequest(
                symbol=symbol,
                market=Market.BIST,
                timeframe=timeframe,
                start=start_date,
                end=dt.date.today(),
            )
        )
        if not fetch.success or fetch.data.empty:
            warnings.append(f"{symbol}: geçerli piyasa verisi bulunamadı; satır üretilmedi.")
            continue
        data = fetch.data
        validation = validator.validate(data, symbol=symbol)
        if not validation.can_run_backtest:
            msg = "; ".join(validation.errors[:2]) or "veri kalite kontrolünden geçemedi"
            warnings.append(f"{symbol}: {msg}; satır üretilmedi.")
            continue

        strategy_results: dict[str, tuple[Any, Any]] = {}
        for strategy_name in set(requested) | {"Al ve Tut"}:
            try:
                _, result, metrics = run_backtest(
                    data,
                    symbol,
                    strategy_name,
                    {},
                    config,
                    timeframe=timeframe.value,
                )
            except ValueError as exc:
                warnings.append(f"{symbol} / {strategy_name}: {exc}")
                continue
            strategy_results[strategy_name] = (result, metrics)

        if "Al ve Tut" not in strategy_results:
            warnings.append(f"{symbol}: Al ve Tut karşılaştırması üretilemedi.")
            continue
        buy_hold_return = strategy_results["Al ve Tut"][1].total_return_pct
        for strategy_name in requested:
            if strategy_name not in strategy_results:
                continue
            result, metrics = strategy_results[strategy_name]
            best_trade_pct, worst_trade_pct, avg_trade_pct = _trade_pct_stats(result)
            trade_volume = _simulated_trade_volume(result)
            cost_total = metrics.total_commission + metrics.total_slippage_cost
            cost_pct = cost_total / initial_capital * 100 if initial_capital else 0.0
            score = (
                metrics.total_return_pct
                - metrics.max_drawdown_pct * 0.55
                + metrics.sharpe_ratio * 10
                + min(metrics.total_trades, 25) * 0.25
                - cost_pct * 0.5
            )
            rows.append(
                {
                    "Sembol": symbol,
                    "Şirket": company,
                    "Strateji": strategy_name,
                    "Net Getiri %": round(metrics.total_return_pct, 2),
                    "Al Tut Fark %": round(metrics.total_return_pct - buy_hold_return, 2),
                    "Final Sermaye": round(metrics.final_equity, 2),
                    "Maks. Düşüş %": round(metrics.max_drawdown_pct, 2),
                    "Sharpe": round(metrics.sharpe_ratio, 2),
                    "Sortino": round(metrics.sortino_ratio, 2),
                    "Kazanma %": round(metrics.win_rate, 2),
                    "Trade": metrics.total_trades,
                    "İşlem Hacmi": round(trade_volume, 2),
                    "Komisyon": round(metrics.total_commission, 2),
                    "Kayma": round(metrics.total_slippage_cost, 2),
                    "Maliyet %": round(cost_pct, 2),
                    "En İyi Trade %": round(best_trade_pct, 2),
                    "En Kötü Trade %": round(worst_trade_pct, 2),
                    "Ort. Trade %": round(avg_trade_pct, 2),
                    "Açık Poz.": "Var" if result.has_open_position else "Yok",
                    "Skor": round(score, 2),
                }
            )
    return pd.DataFrame(rows), warnings


def render_strategy_leaderboard(df: pd.DataFrame):
    if df.empty:
        st.info("Bu filtrelerle gösterilecek strateji sonucu yok.")
        return

    def color_positive(value: float) -> str:
        if pd.isna(value):
            return ""
        return (
            "background-color: rgba(22,199,132,0.18)"
            if value >= 0
            else "background-color: rgba(234,57,67,0.18)"
        )

    def color_drawdown(value: float) -> str:
        if pd.isna(value):
            return ""
        if value <= 10:
            return "background-color: rgba(22,199,132,0.16)"
        if value >= 25:
            return "background-color: rgba(234,57,67,0.20)"
        return "background-color: rgba(240,185,11,0.14)"

    styled = (
        df.style.map(color_positive, subset=["Net Getiri %", "Al Tut Fark %", "Skor"])
        .map(color_drawdown, subset=["Maks. Düşüş %"])
        .format(
            {
                "Net Getiri %": "{:+.2f}",
                "Al Tut Fark %": "{:+.2f}",
                "Final Sermaye": "{:,.0f}",
                "Maks. Düşüş %": "{:.2f}",
                "Sharpe": "{:.2f}",
                "Sortino": "{:.2f}",
                "Kazanma %": "{:.2f}",
                "İşlem Hacmi": "{:,.0f}",
                "Komisyon": "{:,.0f}",
                "Kayma": "{:,.0f}",
                "Maliyet %": "{:.2f}",
                "En İyi Trade %": "{:+.2f}",
                "En Kötü Trade %": "{:+.2f}",
                "Ort. Trade %": "{:+.2f}",
                "Skor": "{:.2f}",
            }
        )
    )
    st.dataframe(
        styled,
        width="stretch",
        hide_index=True,
        height=720,
        key="strategy_leaderboard",
    )


@cache_data
def build_market_matrix(
    symbols: tuple[str, ...],
    start_date_iso: str,
    timeframe_value: str,
) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    warnings: list[str] = []
    config = BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,
        slippage_bps=5,
        max_position_pct=0.95,
    )
    timeframe = Timeframe(timeframe_value)
    start_date = dt.date.fromisoformat(start_date_iso)
    provider = YFinanceProvider(timeout=12)
    validator = DataValidator(min_rows=60)

    for symbol in symbols:
        fetch = provider.fetch_bars(
            BarRequest(
                symbol=symbol,
                market=Market.BIST,
                timeframe=timeframe,
                start=start_date,
                end=dt.date.today(),
            )
        )
        if not fetch.success or fetch.data.empty:
            warnings.append(f"{symbol}: geçerli piyasa verisi bulunamadı; matris satırı atlandı.")
            continue
        data = fetch.data
        validation = validator.validate(data, symbol=symbol)
        if not validation.can_run_backtest:
            msg = "; ".join(validation.errors[:2]) or "veri kalite kontrolünden geçemedi"
            warnings.append(f"{symbol}: {msg}; matris satırı atlandı.")
            continue
        strategy = SmaCrossover(params={"fast_period": 10, "slow_period": 30})
        strategy.prepare(data)
        result = BacktestEngine(config).run(
            data,
            strategy.as_signal_func(),
            symbol=symbol,
        )
        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            config.initial_capital,
            trades=result.trades,
        )
        close = data["close"]
        rsi_val = float(rsi(close, 14).iloc[-1])
        sma20 = float(sma(close, 20).iloc[-1])
        sma50 = float(sma(close, 50).iloc[-1])
        daily_pct = float(close.pct_change().iloc[-1] * 100)
        if close.iloc[-1] > sma20 > sma50:
            trend = "Güçlü yukarı"
        elif close.iloc[-1] < sma20 < sma50:
            trend = "Zayıf"
        else:
            trend = "Kararsız"
        if rsi_val < 35 and trend != "Zayıf":
            signal = "Al izle"
        elif rsi_val > 75:
            signal = "Kar al"
        elif trend == "Zayıf":
            signal = "Riskli"
        else:
            signal = "Bekle"
        score = (
            metrics.total_return_pct
            - metrics.max_drawdown_pct * 0.7
            + metrics.sharpe_ratio * 12
            + min(metrics.total_trades, 20) * 0.4
        )
        rows.append(
            {
                "Sembol": symbol,
                "Şirket": BIST_SYMBOLS.get(symbol, symbol),
                "Son": round(float(close.iloc[-1]), 2),
                "Gün %": round(daily_pct, 2),
                "Trend": trend,
                "RSI": round(rsi_val, 1),
                "Sinyal": signal,
                "Getiri %": round(metrics.total_return_pct, 2),
                "Maks. Düşüş %": round(metrics.max_drawdown_pct, 2),
                "Sharpe": round(metrics.sharpe_ratio, 2),
                "Trade": metrics.total_trades,
                "Skor": round(score, 2),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Skor", ascending=False)
    return df, warnings


def render_matrix_table(df: pd.DataFrame):
    def color_signal(value: str) -> str:
        if value == "Al izle":
            return "background-color: rgba(22,199,132,0.22)"
        if value in {"Kar al", "Riskli"}:
            return "background-color: rgba(234,57,67,0.20)"
        return "background-color: rgba(138,180,255,0.12)"

    def color_score(value: float) -> str:
        if value >= 40:
            return "background-color: rgba(22,199,132,0.24)"
        if value <= -20:
            return "background-color: rgba(234,57,67,0.20)"
        return "background-color: rgba(240,185,11,0.14)"

    def color_drawdown(value: float) -> str:
        if value >= 30:
            return "background-color: rgba(234,57,67,0.24)"
        if value <= 12:
            return "background-color: rgba(22,199,132,0.18)"
        return "background-color: rgba(240,185,11,0.14)"

    styled = (
        df.style.map(color_signal, subset=["Sinyal"])
        .map(color_score, subset=["Skor"])
        .map(color_drawdown, subset=["Maks. Düşüş %"])
        .format(
            {
                "Son": "{:.2f}",
                "Gün %": "{:+.2f}",
                "RSI": "{:.1f}",
                "Getiri %": "{:+.2f}",
                "Maks. Düşüş %": "{:.2f}",
                "Sharpe": "{:.2f}",
                "Skor": "{:.2f}",
            }
        )
    )
    return st.dataframe(
        styled,
        width="stretch",
        hide_index=True,
        height=650,
        key="bist_market_matrix",
        on_select="rerun",
        selection_mode="single-row",
    )


def _selected_dataframe_row(event: Any) -> int | None:
    if isinstance(event, dict):
        rows = event.get("selection", {}).get("rows")
    else:
        selection = getattr(event, "selection", None)
        rows = getattr(selection, "rows", None)
    if not rows:
        return None
    return int(rows[0])


def page_market_matrix():
    st.markdown("## BIST Strateji ve Piyasa Matrisi")
    st.caption(
        "Bu ekran seçili BIST evrenini gerçek piyasa verisiyle tarar, "
        "strateji sonuçlarını büyükten küçüğe sıralar ve piyasa özetini yanında tutar."
    )
    with st.sidebar:
        st.markdown("### Matris Ayarları")
        universe_mode = st.selectbox(
            "Borsa evreni",
            ["BIST 30 hızlı liste", "BIST geniş liste", "BIST çevrimiçi tüm liste"],
            index=0,
        )
        if universe_mode == "BIST 30 hızlı liste":
            universe = BIST30_SYMBOLS
        elif universe_mode == "BIST çevrimiçi tüm liste":
            universe, catalog_warnings = load_online_bist_catalog()
            for warning in catalog_warnings[:3]:
                st.warning(warning)
            st.caption(f"Çevrimiçi katalog: {len(universe)} sembol")
        else:
            universe = BIST_SYMBOLS
        scan_all = st.toggle(
            "Seçili evrenin tamamını tara",
            value=universe_mode == "BIST 30 hızlı liste",
            help=(
                "Geniş listede tüm sembolleri taramak internet hızına ve Yahoo "
                "limitlerine bağlı olarak uzun sürebilir."
            ),
        )
        if scan_all:
            selected_symbols = tuple(universe)
        else:
            selected_labels = st.multiselect(
                "Taranacak semboller",
                [_symbol_label(symbol) for symbol in universe],
                default=[_symbol_label(symbol) for symbol in list(universe)[:30]],
            )
            selected_symbols = tuple(_selected_symbol(label) for label in selected_labels)
        custom_symbols = st.text_input(
            "Ek BIST sembolleri",
            value="",
            help="Listede yoksa virgülle ayır: EREGL, SASA, THYAO. Veri gelmezse satır üretilmez.",
        )
        if custom_symbols.strip():
            custom = tuple(
                item.strip().upper().replace(".IS", "")
                for item in custom_symbols.split(",")
                if item.strip()
            )
            selected_symbols = tuple(dict.fromkeys((*selected_symbols, *custom)))
        timeframe_label = st.selectbox("Zaman dilimi", list(TIMEFRAME_OPTIONS), index=0)
        start_raw = st.text_input("Başlangıç tarihi", value="2022-01-01", key="matrix_start")
        try:
            start_date = dt.date.fromisoformat(start_raw)
        except ValueError:
            start_date = dt.date(2022, 1, 1)
            st.error("Başlangıç tarihi YYYY-AA-GG biçiminde olmalı.")
        st.markdown("### Lider Tablo")
        leader_strategies = st.multiselect(
            "Tablodaki stratejiler",
            list(STRATEGY_MAP),
            default=list(STRATEGY_MAP),
        )
        sort_metric = st.selectbox(
            "Sıralama metriği",
            [
                "Net Getiri %",
                "Skor",
                "Al Tut Fark %",
                "Sharpe",
                "Sortino",
                "İşlem Hacmi",
                "Trade",
                "Komisyon",
                "Maks. Düşüş %",
            ],
        )
        descending = st.toggle("Büyükten küçüğe sırala", value=True)
        min_trades = st.slider("Minimum trade", 0, 30, 0)
        leader_commission = (
            st.slider("Lider komisyon (%)", 0.0, 1.0, 0.1, 0.01) / 100
        )
        leader_slippage = st.slider("Lider kayma (bps)", 0, 50, 5)
        leader_max_pos = st.slider("Lider pozisyon (%)", 10, 100, 95) / 100
        min_score = st.slider("En düşük skor", -80, 80, -80)
        signal_filter = st.multiselect(
            "Sinyal filtresi",
            ["Al izle", "Bekle", "Kar al", "Riskli"],
            default=["Al izle", "Bekle", "Kar al", "Riskli"],
        )
        run_scan = st.button("Gerçek veriyle tara", type="primary", width="stretch")

    if not run_scan:
        st.info(
            "Borsa evrenini ve stratejileri seçip gerçek veri taramasını başlat. "
            "Veri gelmeyen semboller için sonuç üretilmez."
        )
        return

    if not selected_symbols:
        st.warning("Taranacak sembol seçilmedi.")
        return

    timeframe = TIMEFRAME_OPTIONS[timeframe_label]
    leaderboard, leader_warnings = build_strategy_leaderboard(
        tuple(selected_symbols),
        start_date.isoformat(),
        timeframe.value,
        tuple(leader_strategies),
        100_000.0,
        float(leader_commission),
        int(leader_slippage),
        float(leader_max_pos),
    )
    for warning in leader_warnings[:12]:
        st.warning(warning)
    if len(leader_warnings) > 12:
        st.warning(f"{len(leader_warnings) - 12} ek veri uyarısı gizlendi.")
    if min_trades:
        leaderboard = leaderboard[leaderboard["Trade"] >= min_trades]
    if sort_metric in leaderboard:
        leaderboard = leaderboard.sort_values(
            sort_metric,
            ascending=not descending,
            na_position="last",
        )
    leaderboard = leaderboard.reset_index(drop=True)
    if not leaderboard.empty:
        leaderboard.insert(0, "Sıra", np.arange(1, len(leaderboard) + 1))

    df, matrix_warnings = build_market_matrix(
        tuple(selected_symbols),
        start_date.isoformat(),
        timeframe.value,
    )
    for warning in matrix_warnings[:12]:
        st.warning(warning)
    if len(matrix_warnings) > 12:
        st.warning(f"{len(matrix_warnings) - 12} ek matris uyarısı gizlendi.")
    if df.empty:
        st.error("Seçili semboller için geçerli piyasa verisi bulunamadı.")
        return
    df = df[df["Skor"] >= min_score]
    if signal_filter:
        df = df[df["Sinyal"].isin(signal_filter)]

    tab_leader, tab_market = st.tabs(["Strateji Lider Tablosu", "Piyasa Matrisi"])
    with tab_leader:
        if leaderboard.empty:
            st.warning("Seçili strateji veya trade filtresiyle sonuç üretilemedi.")
        else:
            best = leaderboard.iloc[0]
            total_volume = float(leaderboard["İşlem Hacmi"].sum())
            total_commission = float(leaderboard["Komisyon"].sum())
            total_rows = len(leaderboard)
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                render_metric_card("Kombinasyon", total_rows, tone="neutral")
            with k2:
                render_metric_card("Lider Getiri", float(best["Net Getiri %"]), True, "good")
            with k3:
                render_metric_card("İşlem Hacmi", total_volume, tone="neutral")
            with k4:
                render_metric_card("Komisyon", total_commission, tone="warn")
            st.caption(
                f"Lider: {best['Sembol']} / {best['Strateji']} | "
                f"Sıralama: {sort_metric}"
            )
        render_strategy_leaderboard(leaderboard)

    with tab_market:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Sembol", len(df), tone="neutral")
        with c2:
            render_metric_card("Al İzle", int((df["Sinyal"] == "Al izle").sum()), tone="good")
        with c3:
            avg_rsi = float(df["RSI"].mean()) if not df.empty else 0
            render_metric_card("Ort. RSI", avg_rsi, tone="neutral")
        with c4:
            best_score = float(df["Skor"].max()) if not df.empty else 0
            render_metric_card("En iyi skor", best_score, tone="good")

        event = render_matrix_table(df)
        selected_row = _selected_dataframe_row(event)
        if selected_row is not None and selected_row < len(df):
            selected = df.iloc[selected_row]
            st.markdown("### Seçili Sembol Özeti")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                render_metric_card("Sembol", selected["Sembol"])
            with s2:
                render_metric_card("Sinyal", selected["Sinyal"])
            with s3:
                render_metric_card("Skor", float(selected["Skor"]))
            with s4:
                render_metric_card("Getiri", float(selected["Getiri %"]), True)
            st.caption(
                "Sonraki fazda bu seçim ana grafiğe bağlanacak; "
                "şimdilik hızlı karar özeti verir."
            )


def page_backtest_lab():
    st.markdown("## Strateji Laboratuvarı")

    with st.sidebar:
        st.markdown("### Veri ve Sembol")
        symbol_label = st.selectbox(
            "BIST sembolü",
            [_symbol_label(symbol) for symbol in BIST_SYMBOLS],
            index=list(BIST_SYMBOLS).index("THYAO"),
        )
        symbol = _selected_symbol(symbol_label)
        custom_symbol = st.text_input(
            "Özel BIST sembolü",
            value="",
            help="Listede yoksa THYAO, EREGL, SASA gibi kod gir. Veri gelmezse grafik çizilmez.",
        )
        if custom_symbol.strip():
            symbol = custom_symbol.strip().upper().replace(".IS", "")
        timeframe_label = st.selectbox(
            "Zaman dilimi",
            list(TIMEFRAME_OPTIONS),
            index=0,
        )
        start_raw = st.text_input(
            "Başlangıç tarihi",
            value="2022-01-01",
            help="Biçim: YYYY-AA-GG",
        )
        try:
            start_date = dt.date.fromisoformat(start_raw)
        except ValueError:
            start_date = dt.date(2022, 1, 1)
            st.error("Başlangıç tarihi YYYY-AA-GG biçiminde olmalı.")

        st.markdown("### Sermaye ve Maliyet")
        capital = st.number_input(
            "Başlangıç sermayesi",
            min_value=10_000,
            max_value=10_000_000,
            value=100_000,
            step=10_000,
        )
        commission = st.slider("Komisyon (%)", 0.0, 1.0, 0.1, 0.01) / 100
        slippage = st.slider("Kayma (bps)", 0, 50, 5)
        max_pos = st.slider("Maksimum pozisyon (%)", 10, 100, 95) / 100

        st.markdown("### Strateji")
        strategy_name = st.selectbox("Strateji", list(STRATEGY_MAP))
        params: dict[str, Any] = {}
        if strategy_name == "SMA Kesişimi":
            params["fast_period"] = st.slider("Hızlı SMA", 3, 50, 10)
            params["slow_period"] = st.slider("Yavaş SMA", 10, 200, 30)
        elif strategy_name == "RSI Dönüşü":
            params["rsi_period"] = st.slider("RSI periyodu", 5, 30, 14)
            params["oversold"] = st.slider("Aşırı satış", 10, 40, 30)
            params["overbought"] = st.slider("Aşırı alım", 60, 90, 70)
        elif strategy_name == "Bollinger Dönüşü":
            params["period"] = st.slider("Bollinger periyodu", 10, 60, 20)
            params["num_std"] = st.slider("Standart sapma", 1.0, 3.5, 2.0, 0.1)
            exit_label = st.selectbox(
                "Çıkış bandı",
                ["Orta bant", "Üst bant"],
            )
            params["exit_band"] = "upper" if exit_label == "Üst bant" else "middle"

        st.markdown("### Grafik")
        chart_options = ChartOptions(
            show_sma=st.toggle("SMA çizgileri", value=True),
            show_bollinger=st.toggle("Bollinger bantları", value=True),
            show_volume=st.toggle("Hacim paneli", value=True),
            show_equity=st.toggle("Sermaye eğrisi", value=True),
            show_drawdown=st.toggle("Düşüş paneli", value=True),
            show_trade_lines=st.toggle("Trade bağlantıları", value=True),
            log_price=st.toggle("Log fiyat ekseni", value=False),
            range_label=st.selectbox(
                "Hızlı tarih aralığı",
                ["Tümü", "1 Ay", "3 Ay", "6 Ay", "Yıl başı", "1 Yıl"],
            ),
        )
        st.markdown("### JSON Grafik Planı")
        blueprint_indicators = st.multiselect(
            "Planlanacak indikatörler",
            BLUEPRINT_INDICATOR_OPTIONS,
            default=DEFAULT_BLUEPRINT_INDICATORS,
            help="Karar motoru bu listeyi TradingView benzeri grafik katman JSON'una çevirir.",
        )
        run_btn = st.button("Backtest çalıştır", type="primary", width="stretch")

    if not run_btn:
        st.info(
            "Soldaki panelden BIST sembolü, zaman aralığı ve strateji seçip "
            "gerçek veriyle backtest çalıştır."
        )
        return

    timeframe = TIMEFRAME_OPTIONS[timeframe_label]
    data, warnings = load_symbol_data(
        symbol=symbol,
        start_date=start_date,
        timeframe=timeframe,
    )
    for warning in warnings:
        st.warning(warning)
    if data.empty:
        st.error("Veri yüklenemedi. Kaynağı veya tarihi değiştirip tekrar dene.")
        return

    validation = DataValidator(min_rows=30).validate(data, symbol=symbol)
    if not validation.can_run_backtest:
        st.error("Veri kritik hatalar içeriyor; backtest engellendi.")
        for err in validation.errors:
            st.error(err)
        return

    config = BacktestConfig(
        initial_capital=float(capital),
        commission_rate=commission,
        slippage_bps=slippage,
        max_position_pct=max_pos,
    )
    try:
        strategy, result, metrics = run_backtest(
            data,
            symbol,
            strategy_name,
            params,
            config,
            timeframe=timeframe.value,
        )
    except ValueError as exc:
        st.error(f"Parametre hatası: {exc}")
        return

    for warning in result.warnings:
        st.warning(warning)

    left, right = st.columns([0.72, 0.28])
    with left:
        st.markdown(f"### {_symbol_label(symbol)}")
    with right:
        st.metric("Veri Kalitesi", f"{validation.quality_score:.0f}/100")

    render_metric_strip(metrics, result)
    chart_col, detail_col = st.columns([0.72, 0.28])
    with chart_col:
        selected_trade_id = render_market_chart(data, result, symbol, chart_options)
    with detail_col:
        render_strategy_panel(strategy_name, strategy, params)
        render_trade_detail_panel(result, selected_trade_id)

    tab_trades, tab_costs, tab_compare, tab_decision, tab_blueprint, tab_metrics = st.tabs(
        [
            "İşlem Dökümü",
            "Maliyet",
            "Strateji Testi",
            "Karar Motoru",
            "Grafik JSON",
            "Tüm Metrikler",
        ]
    )
    with tab_trades:
        render_trade_table(result)
    with tab_costs:
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Komisyon", metrics.total_commission)
        with c2:
            render_metric_card("Kayma Maliyeti", metrics.total_slippage_cost)
        with c3:
            render_metric_card("Brüt Getiri", metrics.gross_return_pct, True)
    with tab_compare:
        st.caption(
            "Seçili sembolde tüm yerleşik stratejiler aynı veri ve maliyet "
            "varsayımlarıyla test edilir."
        )
        comparison_df = build_strategy_comparison(
            data,
            symbol,
            config,
            timeframe.value,
            strategy_name,
            params,
        )
        render_strategy_comparison(comparison_df)
    with tab_decision:
        st.caption(
            "Bu panel yalnızca doğrulanmış piyasa verisiyle karar üretir. "
            "Veri yetersizse bilinçli olarak VERİ YETERSİZ döndürür."
        )
        decision_report = analyze_market_data(
            data,
            is_real_data=True,
            symbol=symbol,
            timeframe=timeframe_label,
            source_label="Yahoo Finance",
        )
        render_decision_report(decision_report)
    with tab_blueprint:
        st.caption(
            "Bu çıktı frontend tarafından doğrudan parse edilecek katı JSON "
            "formatıdır. Veri yetersizse strateji üretmez."
        )
        blueprint = build_strategy_blueprint(
            data,
            is_real_data=True,
            symbol=symbol,
            timeframe=timeframe_label,
            selected_indicators=tuple(blueprint_indicators),
            source_label="Yahoo Finance",
        )
        render_strategy_blueprint_json(blueprint)
    with tab_metrics:
        st.text(metrics.summary())


def page_optimizer():
    st.markdown("## Parametre Optimizasyonu")
    with st.sidebar:
        st.markdown("### Optimizasyon Ayarları")
        symbol_label = st.selectbox(
            "Sembol",
            [_symbol_label(symbol) for symbol in BIST_SYMBOLS],
            index=list(BIST_SYMBOLS).index("THYAO"),
            key="opt_symbol",
        )
        symbol = _selected_symbol(symbol_label)
        custom_symbol = st.text_input(
            "Özel BIST sembolü",
            value="",
            key="opt_custom_symbol",
            help="Listede yoksa kod gir. Veri gelmezse optimizasyon çalışmaz.",
        )
        if custom_symbol.strip():
            symbol = custom_symbol.strip().upper().replace(".IS", "")
        strategy_name = st.selectbox(
            "Strateji",
            ["SMA Kesişimi", "RSI Dönüşü", "Bollinger Dönüşü"],
            key="opt_strategy",
        )
        timeframe_label = st.selectbox(
            "Zaman dilimi",
            list(TIMEFRAME_OPTIONS),
            index=0,
            key="opt_timeframe",
        )
        start_raw = st.text_input(
            "Başlangıç tarihi",
            value="2022-01-01",
            key="opt_start",
        )
        try:
            start_date = dt.date.fromisoformat(start_raw)
        except ValueError:
            start_date = dt.date(2022, 1, 1)
            st.error("Başlangıç tarihi YYYY-AA-GG biçiminde olmalı.")
        capital = st.number_input(
            "Sermaye",
            10_000,
            10_000_000,
            100_000,
            10_000,
            key="opt_capital",
        )
        ranking = st.selectbox(
            "Sıralama metriği",
            list(RANKING_OPTIONS),
        )
        st.markdown("### Parametre Aralıkları")
        if strategy_name == "SMA Kesişimi":
            fast_values = st.multiselect(
                "Hızlı SMA",
                [5, 10, 15, 20, 25],
                default=[5, 10, 15, 20],
            )
            slow_values = st.multiselect(
                "Yavaş SMA",
                [20, 30, 40, 50, 60, 80, 100],
                default=[20, 30, 40, 50, 60],
            )
            param_grid = {
                "fast_period": fast_values,
                "slow_period": slow_values,
            }
        elif strategy_name == "RSI Dönüşü":
            param_grid = {
                "rsi_period": [7, 14, 21],
                "oversold": [25, 30, 35],
                "overbought": [65, 70, 75],
            }
        else:
            param_grid = {
                "period": [15, 20, 30],
                "num_std": [1.8, 2.0, 2.4],
                "exit_band": ["middle", "upper"],
            }
        run_opt = st.button("Optimizasyonu başlat", type="primary", width="stretch")

    if not run_opt:
        st.info("Optimizasyon yalnızca gerçek piyasa verisi geldikten sonra çalışır.")
        return

    from quant_engine.research.optimizer import GridSearchOptimizer

    timeframe = TIMEFRAME_OPTIONS[timeframe_label]
    data, warnings = load_symbol_data(
        symbol=symbol,
        start_date=start_date,
        timeframe=timeframe,
    )
    for warning in warnings:
        st.warning(warning)
    if data.empty:
        st.error("Geçerli piyasa verisi bulunamadı. Optimizasyon başlatılmadı.")
        return
    validation = DataValidator(min_rows=60).validate(data, symbol=symbol)
    if not validation.can_run_backtest:
        st.error("Veri kritik hatalar içeriyor; optimizasyon engellendi.")
        for err in validation.errors:
            st.error(err)
        return
    config = BacktestConfig(
        initial_capital=float(capital),
        commission_rate=0.001,
        slippage_bps=5,
        max_position_pct=0.95,
    )
    total = int(np.prod([len(v) for v in param_grid.values()]))
    st.info(f"{symbol} için {total} parametre kombinasyonu deneniyor.")
    progress = st.progress(0)

    def update_progress(completed, total_n):
        progress.progress(completed / total_n)

    optimizer = GridSearchOptimizer(config, data, symbol)
    optimizer.set_progress_callback(update_progress)
    strategy_cls = STRATEGY_MAP[strategy_name]
    opt_result = optimizer.run(strategy_cls, param_grid, RANKING_OPTIONS[ranking])
    progress.progress(1.0)

    for warning in opt_result.warnings:
        st.warning(warning)
    df = opt_result.to_dataframe()
    if df.empty:
        st.error("Geçerli parametre kombinasyonu bulunamadı.")
        return
    st.dataframe(df.head(20), width="stretch", hide_index=True)
    if opt_result.best_run:
        st.markdown("### En iyi parametre")
        st.json(opt_result.best_run.params)


def _workspace_symbol_options(market_type: str) -> list[str]:
    if market_type == "Forex":
        return list(FOREX_INSTRUMENTS)
    if market_type == "Emtia":
        return list(COMMODITY_INSTRUMENTS)
    if market_type == "Kripto":
        return list(CRYPTO_INSTRUMENTS)
    if market_type == "BIST 30":
        return list(BIST30_SYMBOLS)
    return list(BIST_SYMBOLS)


def render_workspace_preview(data: pd.DataFrame, symbol: str, precision: int):
    """Gerçek veriden küçük bir önizleme çiz; veri yoksa hiçbir şey üretme."""
    if data.empty:
        st.warning("Veri Bağlantısı Bekleniyor... Gerçek veri gelmeden grafik çizilmez.")
        return
    latest = data.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Son", round(float(latest["close"]), precision), tone="neutral")
    with c2:
        render_metric_card("Yüksek", round(float(latest["high"]), precision), tone="good")
    with c3:
        render_metric_card("Düşük", round(float(latest["low"]), precision), tone="bad")
    with c4:
        render_metric_card("Bar", len(data), tone="neutral")

    if HAS_PLOTLY:
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=data["date"],
                    open=data["open"],
                    high=data["high"],
                    low=data["low"],
                    close=data["close"],
                    name=symbol,
                    increasing_line_color="#16c784",
                    decreasing_line_color="#ea3943",
                )
            ]
        )
        fig.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=12, r=12, t=32, b=12),
            title=f"{symbol} Gerçek Veri Önizleme",
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
        )
        st.plotly_chart(fig, width="stretch")
    st.dataframe(data.tail(20), width="stretch", hide_index=True)


def page_workspace_manager():
    st.markdown("## Çoklu Piyasa Çalışma Alanları")
    st.caption(
        "BIST, Forex, Emtia ve Kripto sembolleri için izole workspace config üretir. "
        "Veri yoksa sahte mum veya rastgele fiyat üretmez."
    )

    with st.sidebar:
        st.markdown("### Workspace Kurulumu")
        market_type = st.selectbox(
            "Piyasa tipi",
            ["BIST 30", "BIST 100", "BIST Tüm", "Forex", "Emtia", "Kripto"],
            index=1,
            key="workspace_market_type",
        )
        symbol_options = _workspace_symbol_options(market_type)
        symbol = st.selectbox(
            "Sembol",
            symbol_options,
            index=symbol_options.index("EREGL") if "EREGL" in symbol_options else 0,
            key=f"workspace_symbol_{market_type}",
        )
        custom_symbol = st.text_input(
            "Özel sembol",
            value="",
            help="Listede yoksa EREGL.IS, USDTRY, XAUUSD, BTCUSDT gibi sembol gir.",
        )
        if custom_symbol.strip():
            symbol = custom_symbol.strip()
        timeframe_label = st.selectbox(
            "Zaman dilimi",
            ["1G", "4S", "1S", "30D", "15D", "5D", "1H", "1A"],
            index=0,
        )
        start_raw = st.text_input(
            "Başlangıç tarihi",
            value="2024-01-01",
            key="workspace_start",
        )
        try:
            start_date = dt.date.fromisoformat(start_raw)
        except ValueError:
            start_date = dt.date(2024, 1, 1)
            st.error("Başlangıç tarihi YYYY-AA-GG biçiminde olmalı.")
        create_btn = st.button(
            "Çalışma alanı oluştur",
            type="primary",
            width="stretch",
        )

    resolution = resolve_workspace(
        WorkspaceRequest(
            symbol_id=symbol,
            market_type=market_type,
            timeframe_label=timeframe_label,
        )
    )
    config_json = build_workspace_config(resolution)
    workspace_state_key = f"workspace:{resolution.workspace_id}:indicators"
    workspace_connect_key = f"workspace:{resolution.workspace_id}:connect"
    if workspace_state_key not in st.session_state:
        st.session_state[workspace_state_key] = ["Mum", "Hacim", "RSI"]
    if create_btn:
        st.session_state[workspace_connect_key] = True

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Workspace", resolution.workspace_id)
    with c2:
        render_metric_card("Sembol", resolution.instrument.symbol_code)
    with c3:
        render_metric_card("Piyasa", resolution.instrument.market_category)
    with c4:
        render_metric_card("Hassasiyet", resolution.instrument.precision)

    selected_indicators = st.multiselect(
        "Bu workspace için indikatörler",
        ["Mum", "Hacim", "SMA 50", "EMA 200", "Bollinger", "RSI", "MACD", "Ichimoku"],
        key=workspace_state_key,
        help=(
            "Bu seçim yalnızca aktif workspace anahtarında tutulur; başka sembole "
            "geçince sıfırdan yüklenir."
        ),
    )
    st.caption(
        f"Aktif izolasyon anahtarı: `{workspace_state_key}` | "
        f"Seçili indikatörler: {', '.join(selected_indicators) or 'Yok'}"
    )

    tab_config, tab_data = st.tabs(["Workspace JSON", "Gerçek Veri Durumu"])
    with tab_config:
        st.code(json.dumps(config_json, ensure_ascii=False, indent=2), language="json")

    with tab_data:
        warning = workspace_warning_text(resolution)
        if warning:
            st.warning(f"Geçerli Piyasa Verisi Bulunamadı: {warning}")
            st.info("Frontend grafiği boş bekleme durumunda tutmalı; sahte OHLC üretilmez.")
            return
        if not st.session_state.get(workspace_connect_key, False):
            st.info("Gerçek veri bağlantısını test etmek için çalışma alanı oluştur.")
            return

        provider = _provider_for_market(resolution.instrument.market, timeout=15)
        result = provider.fetch_bars(
            BarRequest(
                symbol=resolution.instrument.symbol_code,
                market=resolution.instrument.market,
                timeframe=resolution.timeframe,
                start=start_date,
                end=dt.date.today(),
            )
        )
        if not result.success:
            st.warning("Veri Bağlantısı Bekleniyor...")
            for err in result.errors or ["Geçerli piyasa verisi bulunamadı."]:
                st.error(err)
            st.info("Grafik dondurulur; sahte mum veya kopyalanmış bar üretilmez.")
            return
        for warning_item in result.warnings:
            st.warning(warning_item)
        st.success(
            f"{resolution.instrument.symbol_code} için {result.row_count} gerçek bar alındı. "
            f"Kaynak: {result.source}"
        )
        render_workspace_preview(
            result.data,
            resolution.instrument.symbol_code,
            resolution.instrument.precision,
        )


def page_data_station():
    st.markdown("## Veri İstasyonu")
    st.caption(
        "Bu ekran veri kaynağı durumunu, Workspace JSON sözleşmesini ve sembol "
        "gruplarını yönetir. Kaydedilen her kaynak gerçek veri bağlantısı olarak "
        "tanımlanır; demo veri üretmez."
    )
    use_online_catalog = st.toggle(
        "Çevrimiçi tüm BIST kataloğunu dene",
        value=False,
        help="Açılırsa güncel sembol listesi çevrimiçi kaynaktan alınır ve cache'lenir.",
    )
    catalog = BIST_SYMBOLS
    if use_online_catalog:
        catalog, catalog_warnings = load_online_bist_catalog()
        for warning in catalog_warnings[:5]:
            st.warning(warning)
    y_provider = YFinanceProvider(timeout=8)
    b_provider = BinanceProvider(timeout=8)
    workspace_store = WorkspaceJsonStore()
    workspace_doc = workspace_store.load()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("BIST Katalog", len(catalog))
    with c2:
        render_metric_card("Workspace Kaynak", len(workspace_doc["api_sources"]))
    with c3:
        status = "Erişilebilir" if y_provider.health_check() else "Kontrol edilemedi"
        tone = "good" if status == "Erişilebilir" else "warn"
        render_metric_card("Yahoo Durumu", status, tone=tone)
    with c4:
        crypto_status = "Erişilebilir" if b_provider.health_check() else "Kontrol edilemedi"
        render_metric_card("Binance Durumu", crypto_status, tone="good")

    tab_json, tab_sources, tab_groups, tab_catalog = st.tabs(
        ["Workspace JSON", "API Kaynakları", "Sembol Grupları", "BIST Kataloğu"]
    )

    with tab_json:
        st.code(json.dumps(workspace_doc, ensure_ascii=False, indent=2), language="json")

    with tab_sources:
        source_rows = [
            {
                "Ad": item.get("name"),
                "Provider": item.get("provider"),
                "Base URL": item.get("base_url"),
                "Auth": item.get("auth_type"),
                "Aktif": item.get("enabled"),
                "Not": item.get("notes"),
            }
            for item in workspace_doc["api_sources"]
        ]
        st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)
        with st.form("workspace_api_source_form"):
            st.markdown("### Yeni API Kaynağı")
            name = st.text_input("Kaynak adı", value="Özel Kaynak")
            provider_name = st.selectbox(
                "Provider tipi",
                ["yfinance", "binance", "verda", "matriks", "foreks", "custom"],
            )
            base_url = st.text_input("Base URL", value="https://")
            auth_type = st.selectbox("Kimlik doğrulama", ["none", "api_key", "basic", "oauth"])
            enabled = st.toggle("Aktif", value=True)
            notes = st.text_area("Not", value="")
            submitted = st.form_submit_button("Workspace JSON'a ekle", type="primary")
            if submitted:
                workspace_store.upsert_api_source(
                    name=name,
                    provider=provider_name,
                    base_url=base_url,
                    auth_type=auth_type,
                    enabled=enabled,
                    notes=notes,
                )
                st.success("API kaynağı Workspace JSON'a kaydedildi.")
                st.rerun()

    with tab_groups:
        group_rows = [
            {
                "Ad": item.get("name"),
                "Piyasa": item.get("market"),
                "Sembol": ", ".join(item.get("symbols", [])),
            }
            for item in workspace_doc["symbol_groups"]
        ]
        st.dataframe(pd.DataFrame(group_rows), width="stretch", hide_index=True)
        with st.form("workspace_symbol_group_form"):
            st.markdown("### Yeni Sembol Grubu")
            group_name = st.text_input("Grup adı", value="Favoriler")
            group_market = st.selectbox(
                "Piyasa",
                ["bist", "forex", "commodity", "crypto", "mixed"],
            )
            group_symbols = st.text_area(
                "Semboller",
                value="THYAO, SASA, BTCUSDT",
                help="Virgülle ayır.",
            )
            submitted = st.form_submit_button("Sembol grubunu kaydet", type="primary")
            if submitted:
                symbols = [item.strip() for item in group_symbols.split(",")]
                workspace_store.upsert_symbol_group(
                    name=group_name,
                    market=group_market,
                    symbols=symbols,
                )
                st.success("Sembol grubu Workspace JSON'a kaydedildi.")
                st.rerun()

    with tab_catalog:
        st.markdown("### BIST Sembol Kataloğu")
        rows = [
            {"Sembol": symbol, "Şirket": company, "Yahoo Kodu": f"{symbol}.IS"}
            for symbol, company in catalog.items()
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        .stApp {
            background: #0f1117;
            color: #e6edf3;
            font-family: Inter, Arial, sans-serif;
        }
        .stApp > header {
            background: transparent;
        }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"] {
            display: none !important;
            visibility: hidden !important;
        }
        section[data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid rgba(255,255,255,0.08);
            min-width: 310px;
        }
        .block-container {
            padding-top: 1.25rem;
            max-width: 1680px;
        }
        .qe-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 14px;
            margin-bottom: 18px;
        }
        .qe-title {
            margin: 0;
            font-size: 26px;
            color: #f8fafc;
            letter-spacing: 0;
        }
        .qe-subtitle {
            color: #94a3b8;
            font-size: 13px;
            margin-top: 4px;
        }
        .qe-badge {
            color: #16c784;
            border: 1px solid rgba(22,199,132,0.35);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
        }
        .qe-metric {
            background: #151b24;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 12px;
            min-height: 76px;
        }
        .qe-metric-label {
            color: #94a3b8;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 6px;
            white-space: nowrap;
        }
        .qe-metric-value {
            font-size: 22px;
            font-weight: 700;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .qe-info-panel {
            background: #151b24;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .qe-panel-title {
            color: #f8fafc;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .qe-panel-muted {
            color: #94a3b8;
            font-size: 12px;
            line-height: 1.45;
            margin-bottom: 10px;
        }
        .qe-rule {
            color: #dbe4ee;
            font-size: 12px;
            line-height: 1.45;
            margin-top: 6px;
        }
        .qe-risk {
            color: #f0b90b;
            border-top: 1px solid rgba(255,255,255,0.08);
            font-size: 12px;
            line-height: 1.45;
            margin-top: 10px;
            padding-top: 10px;
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        .stButton > button {
            border-radius: 8px;
            font-weight: 700;
        }
        @media (max-width: 900px) {
            section[data-testid="stSidebar"] {
                min-width: 280px;
            }
            .qe-title {
                font-size: 22px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    if not HAS_STREAMLIT:
        print("Streamlit kurulu değil. Kurulum: pip install streamlit")
        return

    st.set_page_config(
        page_title="Quant Trading Terminali",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": None,
            "Report a bug": None,
            "About": (
                "Quant Trading Terminali\n\n"
                "BIST, Forex ve Emtia için gerçek veri odaklı araştırma ekranı."
            ),
        },
    )
    apply_theme()
    st.markdown(
        """
        <div class="qe-header">
            <div>
                <h1 class="qe-title">Quant Trading Terminali</h1>
                <div class="qe-subtitle">
                    BIST, Forex ve Emtia için gerçek veri odaklı araştırma terminali
                </div>
            </div>
            <div class="qe-badge">v0.3 araştırma modu</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.sidebar.radio(
        "Sayfa",
        [
            "Strateji Laboratuvarı",
            "Çalışma Alanları",
            "BIST Matrisi",
            "Optimizasyon",
            "Veri İstasyonu",
        ],
    )
    if page == "Strateji Laboratuvarı":
        page_backtest_lab()
    elif page == "Çalışma Alanları":
        page_workspace_manager()
    elif page == "BIST Matrisi":
        page_market_matrix()
    elif page == "Optimizasyon":
        page_optimizer()
    else:
        page_data_station()


if __name__ == "__main__":
    main()

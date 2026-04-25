"""
Quant Engine — Strateji ve Grafik Kurulum JSON Motoru.

Frontend bu modülün ürettiği sözlüğü doğrudan JSON olarak okuyabilir. Motor,
yalnızca gerçek OHLCV verisiyle strateji planı üretir; gerçek dışı/test verisi
için aynı şemada "Veri Yetersiz" çıktısı verir.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from quant_engine.strategy.indicators import (
    bollinger_bands,
    ema,
    ichimoku_cloud,
    macd,
    rsi,
    sma,
)

Blueprint = dict[str, Any]

DEFAULT_BLUEPRINT_INDICATORS = [
    "Ichimoku",
    "SMA 50",
    "Bollinger Bands",
    "RSI 14",
    "MACD",
    "Hacim",
    "Sermaye Eğrisi",
    "Drawdown",
]

BLUEPRINT_INDICATOR_OPTIONS = [
    "Ichimoku",
    "SMA 20",
    "SMA 50",
    "SMA 200",
    "EMA 200",
    "Bollinger Bands",
    "RSI 14",
    "MACD",
    "Hacim",
    "Sermaye Eğrisi",
    "Drawdown",
]


def insufficient_blueprint(reason: str) -> Blueprint:
    """Parse edilebilir sabit şemada veri reddi üret."""
    return {
        "planlama_ve_analiz": {
            "arastirma_adimi": (
                "Veri Yetersiz. Gerçek OHLCV ve seçili indikatör değerleri "
                f"doğrulanamadı: {reason}"
            ),
            "strateji_kurgusu": (
                "Gerçek dışı, statik veya eksik veriyle profesyonel AL/SAT kurgusu "
                "üretilmedi. Frontend sadece boş/korumalı grafik şablonunu "
                "göstermeli ve kullanıcıdan gerçek veri seçmesini istemeli."
            ),
        },
        "strateji_bilgileri": {
            "strateji_adi": "Veri Yetersiz - Strateji Üretilmedi",
            "kullanici_aciklamasi": (
                "Bu ekran canlı/gerçek veri olmadan sinyal üretmez. Gerçek "
                "veri kaynağı seçilip yeterli bar geldiğinde strateji haritası "
                "oluşturulur."
            ),
            "al_kosulu": "Veri Yetersiz: AL koşulu oluşturulmadı.",
            "sat_kosulu": "Veri Yetersiz: SAT/KÂR AL koşulu oluşturulmadı.",
        },
        "grafik_kurulum_haritasi": {
            "ana_grafik_overlay": [
                {
                    "gorsel_tipi": "Mum Grafik (Candlesticks)",
                    "veri": "Gerçek OHLC bekleniyor",
                }
            ],
            "alt_pencereler_subcharts": [],
        },
    }


def _contains(indicators: list[str], needle: str) -> bool:
    return any(needle.lower() in item.lower() for item in indicators)


def _periods_for(indicators: list[str], prefix: str) -> list[int]:
    periods: list[int] = []
    pattern = re.compile(rf"{re.escape(prefix)}\s*(\d+)", flags=re.IGNORECASE)
    for item in indicators:
        match = pattern.search(item)
        if match:
            periods.append(int(match.group(1)))
    return periods


def _fmt(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _latest(series: pd.Series) -> float:
    value = float(series.iloc[-1])
    if not np.isfinite(value):
        raise ValueError("son indikatör değeri geçersiz")
    return value


def _required_rows(indicators: list[str]) -> int:
    required = 30
    if _contains(indicators, "Ichimoku"):
        required = max(required, 52 + 26 + 1)
    for period in _periods_for(indicators, "SMA"):
        required = max(required, period + 1)
    for period in _periods_for(indicators, "EMA"):
        required = max(required, period + 1)
    if _contains(indicators, "Bollinger"):
        required = max(required, 21)
    if _contains(indicators, "RSI"):
        required = max(required, 15)
    if _contains(indicators, "MACD"):
        required = max(required, 35)
    return required


def _indicator_research(indicators: list[str], values: dict[str, float]) -> str:
    parts = [
        "TradingView tarzı ekranda fiyat mumları ana pane'de, osilatörler ve "
        "performans serileri ayrı alt pencerelerde tutulmalıdır."
    ]
    if _contains(indicators, "Ichimoku"):
        parts.append(
            "Ichimoku trend, momentum ve destek/direnç bilgisini aynı overlay'de "
            "verir; bulutun üstü yükseliş rejimi, altı zayıf rejim olarak okunur."
        )
    if _periods_for(indicators, "SMA") or _periods_for(indicators, "EMA"):
        parts.append(
            "SMA/EMA çizgileri fiyatın ana yönünü ve ortalamadan sapmayı "
            "filtrelemek için kullanılır."
        )
    if _contains(indicators, "Bollinger"):
        parts.append(
            "Bollinger bantları volatilite genişlemesini ve fiyatın istatistiksel "
            "uç bölgelere yaklaşıp yaklaşmadığını gösterir."
        )
    if _contains(indicators, "RSI"):
        parts.append(
            "RSI 14 momentumun aşırı alım/aşırı satım bölgesinde mi yoksa "
            "50 eşiği üzerinde güçleniyor mu sorusunu yanıtlar."
        )
    if _contains(indicators, "MACD"):
        parts.append(
            "MACD trend momentumu ve sinyal çizgisi kesişimiyle geç kalan ama "
            "daha temiz teyit üretir."
        )
    if _contains(indicators, "Hacim"):
        parts.append(
            "Hacim, kırılım veya dönüş sinyalinin piyasa katılımıyla desteklenip "
            "desteklenmediğini filtreler."
        )
    if values:
        parts.append(
            "Son gerçek bar özeti: "
            + ", ".join(f"{key}={_fmt(value)}" for key, value in values.items())
            + "."
        )
    return " ".join(parts)


def _strategy_name(indicators: list[str]) -> str:
    if _contains(indicators, "Ichimoku") and _contains(indicators, "Bollinger"):
        return "Bulut Trendinde Volatilite Dönüş Stratejisi"
    if _contains(indicators, "MACD") and _contains(indicators, "RSI"):
        return "Çift Momentum Onaylı Trend Stratejisi"
    return "Çoklu İndikatör Onaylı BIST Stratejisi"


def _strategy_rules(indicators: list[str]) -> tuple[str, str, str]:
    trend_rules: list[str] = []
    buy_rules: list[str] = []
    sell_rules: list[str] = []

    if _contains(indicators, "Ichimoku"):
        trend_rules.append(
            "Ichimoku ana trend filtresi olur; fiyat bulut üstünde ise sadece "
            "AL fırsatları, bulut altında ise SAT/kaçınma senaryoları öncelenir."
        )
        buy_rules.append("Fiyat Ichimoku bulutunun üzerinde kapanmalı")
        sell_rules.append("Fiyat bulut içine geri dönmeli veya bulut altında kapanmalı")

    for period in _periods_for(indicators, "SMA"):
        buy_rules.append(f"Fiyat SMA {period} üzerinde kapanmalı")
        sell_rules.append(f"Fiyat SMA {period} altına sarkmalı")
    for period in _periods_for(indicators, "EMA"):
        buy_rules.append(f"Fiyat EMA {period} üzerinde kalmalı")
        sell_rules.append(f"Fiyat EMA {period} altına inmeli")

    if _contains(indicators, "Bollinger"):
        trend_rules.append(
            "Bollinger stop ve hedef alanını belirler; alt bant dönüş, orta bant "
            "ilk hedef, üst bant kâr alma bölgesi olarak kullanılır."
        )
        buy_rules.append("Fiyat Bollinger alt/orta bölgeden yukarı tepki üretmeli")
        sell_rules.append("Fiyat Bollinger üst banda yaklaşmalı veya orta bandı aşağı kırmalı")

    if _contains(indicators, "RSI"):
        trend_rules.append(
            "RSI tetikleyici momentum filtresidir; 50 üzeri güçlenme, 70 üstü "
            "yorulma olarak yorumlanır."
        )
        buy_rules.append("RSI 14 50 üzerine çıkmalı veya 30 bölgesinden yukarı dönmeli")
        sell_rules.append("RSI 14 70 üzerinde yorulmalı veya 50 altına dönmeli")

    if _contains(indicators, "MACD"):
        trend_rules.append(
            "MACD ikincil teyittir; histogramın pozitife dönmesi AL sinyalini, "
            "negatife dönmesi SAT sinyalini filtreler."
        )
        buy_rules.append("MACD çizgisi sinyal çizgisinin üzerine geçmeli")
        sell_rules.append("MACD çizgisi sinyal çizgisinin altına geçmeli")

    if _contains(indicators, "Hacim"):
        buy_rules.append("AL barındaki hacim son ortalamanın üzerinde olmalı")
        sell_rules.append("SAT/kâr alma barında hacim artışı zayıflamayı onaylamalı")

    if not buy_rules:
        buy_rules.append("Seçili indikatör seti AL koşulu için yetersiz")
    if not sell_rules:
        sell_rules.append("Seçili indikatör seti SAT koşulu için yetersiz")
    if not trend_rules:
        trend_rules.append(
            "Seçili indikatörler trend, momentum veya volatiliteyi yeterince "
            "ayırmadığı için strateji yalnızca izleme modunda kalmalıdır."
        )

    return " ".join(trend_rules), " VE ".join(buy_rules), " VE ".join(sell_rules)


def _main_overlays(indicators: list[str]) -> list[dict[str, str]]:
    overlays = [
        {
            "gorsel_tipi": "Mum Grafik (Candlesticks)",
            "veri": "Açılış, Yüksek, Düşük, Kapanış (OHLC)",
        }
    ]
    if _contains(indicators, "Ichimoku"):
        overlays.append(
            {
                "gorsel_tipi": "İndikatör Çizimi",
                "isim": "Ichimoku Bulutu",
                "parametreler": "9, 26, 52, 26",
                "stil": "Bulut içi yeşil/kırmızı dolgulu, Tenkan ve Kijun çizgileri belirgin",
                "amaci": "Ana trend yönü, destek/direnç ve trend rejimi tespiti",
            }
        )
    for period in _periods_for(indicators, "SMA"):
        overlays.append(
            {
                "gorsel_tipi": "İndikatör Çizimi",
                "isim": f"SMA {period}",
                "parametreler": str(period),
                "stil": "Ana fiyat üstünde ince mavi çizgi",
                "amaci": "Trend filtresi ve dinamik destek/direnç",
            }
        )
    for period in _periods_for(indicators, "EMA"):
        overlays.append(
            {
                "gorsel_tipi": "İndikatör Çizimi",
                "isim": f"EMA {period}",
                "parametreler": str(period),
                "stil": "Ana fiyat üstünde sarı çizgi",
                "amaci": "Ana yön ve uzun vadeli trend filtresi",
            }
        )
    if _contains(indicators, "Bollinger"):
        overlays.append(
            {
                "gorsel_tipi": "İndikatör Çizimi",
                "isim": "Bollinger Bands",
                "parametreler": "20, 2.0",
                "stil": "Üst/alt bant açık mavi, orta bant kesikli, bant arası şeffaf dolgu",
                "amaci": "Volatilite, dönüş bölgesi, stop ve hedef alanları",
            }
        )
    overlays.append(
        {
            "gorsel_tipi": "Sinyal İşaretçileri (Markers)",
            "isim": "AL / SAT Okları",
            "stil": (
                "AL için mum altında yeşil yukarı ok, SAT için mum üstünde kırmızı "
                "aşağı ok, yanlarında net getiri/zarar %'si"
            ),
        }
    )
    return overlays


def _subcharts(indicators: list[str]) -> list[dict[str, Any]]:
    panes: list[dict[str, Any]] = []
    order = 1
    if _contains(indicators, "Hacim"):
        panes.append(
            {
                "pencere_sirasi": order,
                "isim": "Hacim (Volume)",
                "gorsel_tipi": "Histogram",
                "stil": "Yükseliş günlerinde yeşil, düşüş günlerinde kırmızı barlar",
            }
        )
        order += 1
    if _contains(indicators, "RSI"):
        panes.append(
            {
                "pencere_sirasi": order,
                "isim": "RSI",
                "gorsel_tipi": "Çizgi Grafik ve Alan",
                "parametreler": "14",
                "stil": "30 ve 70 seviyelerinde referans çizgileri, arkaplan hafif mor dolgulu",
            }
        )
        order += 1
    if _contains(indicators, "MACD"):
        panes.append(
            {
                "pencere_sirasi": order,
                "isim": "MACD",
                "gorsel_tipi": "Çizgi Grafik ve Histogram",
                "parametreler": "12, 26, 9",
                "stil": "MACD çizgisi mavi, sinyal çizgisi turuncu, histogram yeşil/kırmızı",
            }
        )
        order += 1
    if _contains(indicators, "Sermaye"):
        panes.append(
            {
                "pencere_sirasi": order,
                "isim": "Sermaye Eğrisi",
                "gorsel_tipi": "Çizgi Grafik",
                "icerik": "Backtest sermaye eğrisi, pozitif eğim yeşil çizgi",
            }
        )
        order += 1
    if _contains(indicators, "Drawdown"):
        panes.append(
            {
                "pencere_sirasi": order,
                "isim": "Maksimum Düşüş / Drawdown",
                "gorsel_tipi": "Alan Grafik",
                "icerik": "Sermaye zirvesinden düşüş yüzdesi, kırmızı negatif alan",
            }
        )
    return panes


def _latest_values(data: pd.DataFrame, indicators: list[str]) -> dict[str, float]:
    close = pd.to_numeric(data["close"], errors="coerce")
    high = pd.to_numeric(data["high"], errors="coerce")
    low = pd.to_numeric(data["low"], errors="coerce")
    values: dict[str, float] = {"Fiyat": float(close.iloc[-1])}
    for period in _periods_for(indicators, "SMA"):
        values[f"SMA {period}"] = _latest(sma(close, period))
    for period in _periods_for(indicators, "EMA"):
        values[f"EMA {period}"] = _latest(ema(close, period))
    if _contains(indicators, "Bollinger"):
        upper, middle, lower = bollinger_bands(close, 20, 2.0)
        values["BB Alt"] = _latest(lower)
        values["BB Orta"] = _latest(middle)
        values["BB Üst"] = _latest(upper)
    if _contains(indicators, "RSI"):
        values["RSI 14"] = _latest(rsi(close, 14))
    if _contains(indicators, "MACD"):
        macd_line, signal_line, histogram = macd(close)
        values["MACD"] = _latest(macd_line)
        values["MACD Sinyal"] = _latest(signal_line)
        values["MACD Histogram"] = _latest(histogram)
    if _contains(indicators, "Ichimoku"):
        cloud = ichimoku_cloud(high, low, close)
        values["Tenkan"] = _latest(cloud["tenkan_sen"])
        values["Kijun"] = _latest(cloud["kijun_sen"])
        values["Senkou A"] = _latest(cloud["senkou_span_a"])
        values["Senkou B"] = _latest(cloud["senkou_span_b"])
    if _contains(indicators, "Hacim"):
        values["Hacim"] = float(pd.to_numeric(data["volume"], errors="coerce").iloc[-1])
    return values


def build_strategy_blueprint(
    data: pd.DataFrame,
    *,
    is_real_data: bool,
    symbol: str,
    timeframe: str,
    selected_indicators: list[str] | tuple[str, ...],
    source_label: str,
) -> Blueprint:
    """Seçili indikatörlere göre strateji ve grafik katmanı JSON'u üret."""
    indicators = list(selected_indicators) or DEFAULT_BLUEPRINT_INDICATORS
    if not is_real_data:
        return insufficient_blueprint(
            f"{source_label} gerçek piyasa verisi olarak işaretlenmedi."
        )

    required_columns = {"date", "open", "high", "low", "close", "volume"}
    missing = sorted(required_columns - set(data.columns))
    if missing:
        return insufficient_blueprint(f"Eksik OHLCV kolonları: {', '.join(missing)}.")

    required_rows = _required_rows(indicators)
    if len(data) < required_rows:
        return insufficient_blueprint(
            f"Seçili indikatörler için en az {required_rows} bar gerçek veri gerekli."
        )

    clean = data.sort_values("date").copy()
    try:
        values = _latest_values(clean, indicators)
    except (ValueError, IndexError):
        return insufficient_blueprint("Son indikatör değerleri hesaplanamadı.")

    trend_plan, buy_condition, sell_condition = _strategy_rules(indicators)
    latest_time = pd.Timestamp(clean.iloc[-1]["date"]).strftime("%Y-%m-%d %H:%M")
    strategy_name = _strategy_name(indicators)
    research = _indicator_research(indicators, values)
    strategy_setup = (
        f"{symbol} için {timeframe} zaman diliminde son gerçek bar {latest_time}. "
        f"{trend_plan} AL sinyali yalnızca trend filtresi, momentum/volatilite "
        "teyidi ve hacim onayı aynı yönde olduğunda çizilir; aksi halde frontend "
        "BEKLE durumunu korur."
    )

    return {
        "planlama_ve_analiz": {
            "arastirma_adimi": research,
            "strateji_kurgusu": strategy_setup,
        },
        "strateji_bilgileri": {
            "strateji_adi": strategy_name,
            "kullanici_aciklamasi": (
                f"{strategy_name}, seçili indikatörleri tek tek sinyal üretmek "
                "için değil, birbirini doğrulayan katmanlar olarak kullanır. "
                "Ana grafik trend ve fiyat bölgesini gösterir; alt pencereler "
                "momentum, hacim ve performans doğrulamasını taşır."
            ),
            "al_kosulu": buy_condition,
            "sat_kosulu": sell_condition,
        },
        "grafik_kurulum_haritasi": {
            "ana_grafik_overlay": _main_overlays(indicators),
            "alt_pencereler_subcharts": _subcharts(indicators),
        },
    }

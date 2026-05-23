"""
Quant Engine — Strateji Analiz ve Karar Motoru.

Bu modül backtest stratejisi değildir; doğrulanmış kaynak verisiyle beslenen son barı
EMA 200, Bollinger Bands ve RSI 14 füzyonuyla yorumlayan karar katmanıdır.
Doğrulanmamış veya test fixture verisiyle karar üretmez.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from quant_engine.strategy.indicators import bollinger_bands, ema, rsi

Decision = Literal["AL", "SAT", "BEKLE", "VERİ YETERSİZ"]


@dataclass(frozen=True)
class IndicatorSnapshot:
    """Karar motoruna verilen son bar ve indikatör özeti."""

    symbol: str
    timeframe: str
    latest_time: str
    current_price: float
    volume: float
    ema200: float
    bb_lower: float
    bb_middle: float
    bb_upper: float
    rsi14: float
    prev_rsi14: float


@dataclass(frozen=True)
class DecisionReport:
    """Loglanabilir, UI'da gösterilebilir karar çıktısı."""

    decision: Decision
    strategy_type: str
    trend_control: str
    volatility_momentum: str
    stop_loss: str
    take_profit: str
    data_status: str
    snapshot: IndicatorSnapshot | None = None

    def to_log_text(self) -> str:
        """Kullanıcının istediği standart metin formatında çıktı üret."""
        return (
            f"KARAR: {self.decision}\n"
            f"STRATEJİ TÜRÜ: {self.strategy_type}\n\n"
            "STRATEJİ MANTIĞI VE BİRLEŞTİRME DETAYLARI:\n"
            f"- Trend Kontrolü: {self.trend_control}\n"
            f"- Volatilite ve Momentum Kesişimi: {self.volatility_momentum}\n\n"
            "RİSK YÖNETİMİ:\n"
            f"- SL (Zarar Kes): {self.stop_loss}\n"
            f"- TP (Kâr Al): {self.take_profit}\n"
        )


def insufficient_report(reason: str) -> DecisionReport:
    """Eksik veya gerçek olmayan veri için standart reddetme çıktısı."""
    return DecisionReport(
        decision="VERİ YETERSİZ",
        strategy_type="Veri reddi",
        trend_control=reason,
        volatility_momentum=(
            "Trend, volatilite ve momentum metrikleri aynı gerçek veri "
            "setinden doğrulanamadığı için sinyal üretilmedi."
        ),
        stop_loss="Belirlenmedi; geçerli işlem sinyali yok.",
        take_profit="Belirlenmedi; geçerli işlem sinyali yok.",
        data_status=reason,
    )


def _fmt(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _valid_numbers(values: list[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def analyze_indicator_snapshot(
    snapshot: IndicatorSnapshot,
    *,
    is_real_data: bool,
    source_label: str = "Doğrulanmış kaynak verisi",
) -> DecisionReport:
    """
    Verilmiş indikatör değerleriyle AL/SAT/BEKLE kararı üret.

    Tek indikatörle karar verilmez. Trend filtresi EMA 200, volatilite
    filtresi Bollinger Bands, momentum filtresi RSI 14 ile birlikte okunur.
    """
    if not is_real_data:
        return insufficient_report(
            f"{source_label} gerçek piyasa verisi olarak işaretlenmedi. "
            "Karar motoru gerçek dışı veya test fixture verisiyle çalışmaz."
        )

    values = [
        snapshot.current_price,
        snapshot.volume,
        snapshot.ema200,
        snapshot.bb_lower,
        snapshot.bb_middle,
        snapshot.bb_upper,
        snapshot.rsi14,
        snapshot.prev_rsi14,
    ]
    if not _valid_numbers(values) or snapshot.volume <= 0:
        return insufficient_report(
            "Güncel fiyat, hacim veya indikatör değerlerinden en az biri eksik/geçersiz."
        )

    price = float(snapshot.current_price)
    ema200 = float(snapshot.ema200)
    lower = float(snapshot.bb_lower)
    middle = float(snapshot.bb_middle)
    upper = float(snapshot.bb_upper)
    rsi_now = float(snapshot.rsi14)
    rsi_prev = float(snapshot.prev_rsi14)
    band_width = max(upper - lower, 1e-9)
    band_position = (price - lower) / band_width

    trend_up = price > ema200
    trend_down = price < ema200
    near_lower_band = price <= lower * 1.01 or band_position <= 0.20
    near_upper_band = price >= upper * 0.99 or band_position >= 0.80
    rsi_rebound = (rsi_prev < 30 <= rsi_now) or (
        rsi_now > rsi_prev and 30 <= rsi_now <= 45
    )
    rsi_overheated = rsi_now >= 70 or (rsi_now < rsi_prev and rsi_now >= 60)

    if trend_up and near_lower_band and rsi_rebound:
        decision: Decision = "AL"
        strategy_type = "Trend İçi Volatilite Dönüşü (EMA 200 + Bollinger + RSI)"
    elif near_upper_band and rsi_overheated:
        decision = "SAT"
        strategy_type = "Aşırı Uzanım Kâr Alma (EMA 200 + Bollinger + RSI)"
    elif trend_down and price < middle and rsi_now <= 50:
        decision = "SAT"
        strategy_type = "Trend Zayıflama Çıkışı (EMA 200 + Bollinger + RSI)"
    else:
        decision = "BEKLE"
        strategy_type = "Onay Bekleyen Füzyon (EMA 200 + Bollinger + RSI)"

    trend_direction = "YUKARI" if trend_up else "AŞAĞI"
    trend_control = (
        f"{snapshot.symbol} {snapshot.timeframe} son fiyatı {_fmt(price)}; "
        f"EMA 200 {_fmt(ema200)}. Fiyat EMA 200'ün "
        f"{'üzerinde' if trend_up else 'altında'} olduğu için ana yön "
        f"{trend_direction} kabul edildi. Son bar: {snapshot.latest_time}."
    )

    if near_lower_band:
        band_text = "fiyat Bollinger alt banda/alt bölgeye yakın"
    elif near_upper_band:
        band_text = "fiyat Bollinger üst banda/üst bölgeye yakın"
    else:
        band_text = "fiyat Bollinger bandının orta bölgesinde"

    if rsi_rebound:
        rsi_text = "RSI aşırı satıştan toparlanıyor"
    elif rsi_overheated:
        rsi_text = "RSI aşırı alım/yorulma bölgesinde"
    else:
        rsi_text = "RSI henüz net dönüş onayı vermiyor"

    volatility_momentum = (
        f"Bollinger alt/orta/üst değerleri {_fmt(lower)} / {_fmt(middle)} / "
        f"{_fmt(upper)}. {band_text}; RSI 14 {rsi_prev:.1f} değerinden "
        f"{rsi_now:.1f} değerine geldi. {rsi_text}. Karar, EMA trend filtresi "
        "ile Bollinger volatilite bölgesi ve RSI momentum dönüşü beraber "
        "okunarak üretildi."
    )

    if decision == "AL":
        stop_loss = (
            f"Bollinger alt bandının %1 altı: {_fmt(lower * 0.99)}. "
            "Fiyat bu seviyenin altında kapanırsa volatilite dönüş tezi bozulur."
        )
        take_profit = (
            f"İlk hedef Bollinger orta bandı: {_fmt(middle)}; güçlü devamda "
            f"üst bant: {_fmt(upper)}."
        )
    elif decision == "SAT":
        stop_loss = (
            f"SAT/çıkış kararı geçersizliği için üst bandın %1 üzeri "
            f"{_fmt(upper * 1.01)} takip edilir. Bu karar spot pozisyon "
            "kapatma/azaltma olarak yorumlanır."
        )
        take_profit = (
            f"İlk geri çekilme hedefi Bollinger orta bandı: {_fmt(middle)}; "
            f"zayıf trendde EMA 200 bölgesi: {_fmt(ema200)}."
        )
    else:
        stop_loss = "Belirlenmedi; üçlü indikatör onayı oluşmadığı için pozisyon açılmaz."
        take_profit = "Belirlenmedi; AL/SAT sinyali yerine bekleme kararı üretildi."

    return DecisionReport(
        decision=decision,
        strategy_type=strategy_type,
        trend_control=trend_control,
        volatility_momentum=volatility_momentum,
        stop_loss=stop_loss,
        take_profit=take_profit,
        data_status=f"{source_label} ile analiz edildi.",
        snapshot=snapshot,
    )


def analyze_market_data(
    data: pd.DataFrame,
    *,
    is_real_data: bool,
    symbol: str,
    timeframe: str,
    source_label: str,
) -> DecisionReport:
    """OHLCV verisinden indikatörleri hesaplayıp karar raporu üret."""
    if not is_real_data:
        return insufficient_report(
            f"{source_label} gerçek piyasa verisi değildir. Gerçek dışı/test verisiyle "
            "karar motoru çalıştırılmaz."
        )
    required = {"close", "volume"}
    missing = sorted(required - set(data.columns))
    if missing:
        return insufficient_report(f"Eksik kolonlar: {', '.join(missing)}.")
    if len(data) < 201:
        return insufficient_report(
            "EMA 200, Bollinger ve RSI füzyonu için en az 201 bar gerçek veri gerekli."
        )

    clean = data.sort_values("date") if "date" in data.columns else data.copy()
    close = pd.to_numeric(clean["close"], errors="coerce")
    volume = pd.to_numeric(clean["volume"], errors="coerce")
    ema200 = ema(close, 200)
    bb_upper, bb_middle, bb_lower = bollinger_bands(close, 20, 2.0)
    rsi14 = rsi(close, 14)
    last = clean.iloc[-1]
    latest_time = (
        pd.Timestamp(last["date"]).strftime("%Y-%m-%d %H:%M")
        if "date" in clean.columns
        else str(clean.index[-1])
    )
    snapshot = IndicatorSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        latest_time=latest_time,
        current_price=float(close.iloc[-1]),
        volume=float(volume.iloc[-1]),
        ema200=float(ema200.iloc[-1]),
        bb_lower=float(bb_lower.iloc[-1]),
        bb_middle=float(bb_middle.iloc[-1]),
        bb_upper=float(bb_upper.iloc[-1]),
        rsi14=float(rsi14.iloc[-1]),
        prev_rsi14=float(rsi14.iloc[-2]),
    )
    return analyze_indicator_snapshot(
        snapshot,
        is_real_data=True,
        source_label=source_label,
    )

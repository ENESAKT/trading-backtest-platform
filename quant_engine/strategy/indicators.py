"""
Quant Engine — Teknik İndikatörler

pandas-ta yerine kendi yazdığımız saf NumPy/Pandas indikatörler.
Dış bağımlılık yok, kontrol tamamen bizde.

Desteklenen indikatörler:
    - SMA (Simple Moving Average)
    - EMA (Exponential Moving Average)
    - RSI (Relative Strength Index)
    - Bollinger Bands
    - ATR (Average True Range)
    - MACD (Moving Average Convergence Divergence)

Kullanım:
    from quant_engine.strategy.indicators import sma, ema, rsi

    df["sma_20"] = sma(df["close"], 20)
    df["rsi_14"] = rsi(df["close"], 14)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average (Basit Hareketli Ortalama).

    Args:
        series: Fiyat serisi
        period: Periyot (bar sayısı)

    Returns:
        pd.Series: SMA değerleri (ilk period-1 bar NaN)
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average (Üstel Hareketli Ortalama).

    Args:
        series: Fiyat serisi
        period: Periyot

    Returns:
        pd.Series: EMA değerleri
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Wilder's smoothing method (EMA with alpha=1/period).

    Args:
        series: Fiyat serisi (genellikle close)
        period: Periyot (varsayılan 14)

    Returns:
        pd.Series: RSI değerleri (0-100 arası)
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")

    delta = series.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder's smoothing
    avg_gain = gain.ewm(
        alpha=1.0 / period, min_periods=period, adjust=False
    ).mean()
    avg_loss = loss.ewm(
        alpha=1.0 / period, min_periods=period, adjust=False
    ).mean()

    # RS ve RSI
    rs = avg_gain / avg_loss.replace(0, np.inf)
    result = 100.0 - (100.0 / (1.0 + rs))

    # avg_loss == 0 → RSI = 100 (tam yükseliş)
    result = result.where(avg_loss > 0, 100.0)
    # İlk period bar NaN
    result.iloc[:period] = np.nan

    return result


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bantları.

    Args:
        series: Fiyat serisi
        period: SMA periyodu (varsayılan 20)
        num_std: Standart sapma çarpanı (varsayılan 2)

    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    middle = sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Average True Range.

    Args:
        high: Yüksek fiyat serisi
        low: Düşük fiyat serisi
        close: Kapanış fiyat serisi
        period: Periyot (varsayılan 14)

    Returns:
        pd.Series: ATR değerleri
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(
        alpha=1.0 / period, min_periods=period, adjust=False
    ).mean()


def macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence).

    Args:
        series: Fiyat serisi
        fast_period: Hızlı EMA periyodu (varsayılan 12)
        slow_period: Yavaş EMA periyodu (varsayılan 26)
        signal_period: Sinyal EMA periyodu (varsayılan 9)

    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    fast_ema = ema(series, fast_period)
    slow_ema = ema(series, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

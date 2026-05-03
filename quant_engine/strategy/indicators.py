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


def ichimoku_cloud(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    conversion_period: int = 9,
    base_period: int = 26,
    span_b_period: int = 52,
    displacement: int = 26,
) -> dict[str, pd.Series]:
    """
    Ichimoku Bulutu bileşenleri.

    Returns:
        dict: tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
    """
    if min(conversion_period, base_period, span_b_period, displacement) < 1:
        raise ValueError("Ichimoku periyotları 1'den küçük olamaz.")

    tenkan_sen = (
        high.rolling(conversion_period, min_periods=conversion_period).max()
        + low.rolling(conversion_period, min_periods=conversion_period).min()
    ) / 2
    kijun_sen = (
        high.rolling(base_period, min_periods=base_period).max()
        + low.rolling(base_period, min_periods=base_period).min()
    ) / 2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    senkou_span_b = (
        (
            high.rolling(span_b_period, min_periods=span_b_period).max()
            + low.rolling(span_b_period, min_periods=span_b_period).min()
        )
        / 2
    ).shift(displacement)
    chikou_span = close.shift(-displacement)
    return {
        "tenkan_sen": tenkan_sen,
        "kijun_sen": kijun_sen,
        "senkou_span_a": senkou_span_a,
        "senkou_span_b": senkou_span_b,
        "chikou_span": chikou_span,
    }


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


def wma(series: pd.Series, period: int) -> pd.Series:
    """
    Weighted Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    weights = np.arange(1, period + 1)

    def apply_wma(x):
        if len(x) < period:
            return np.nan
        return np.dot(x, weights) / weights.sum()

    return series.rolling(window=period, min_periods=period).apply(apply_wma, raw=True)


def dema(series: pd.Series, period: int) -> pd.Series:
    """
    Double Exponential Moving Average.
    """
    ema1 = ema(series, period)
    ema2 = ema(ema1, period)
    return 2 * ema1 - ema2


def tema(series: pd.Series, period: int) -> pd.Series:
    """
    Triple Exponential Moving Average.
    """
    ema1 = ema(series, period)
    ema2 = ema(ema1, period)
    ema3 = ema(ema2, period)
    return 3 * ema1 - 3 * ema2 + ema3


def zlema(series: pd.Series, period: int) -> pd.Series:
    """
    Zero-Lag Exponential Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    lag = int((period - 1) / 2)
    shifted_series = series.shift(lag)
    data = series + (series - shifted_series)
    return ema(data, period)


def hma(series: pd.Series, period: int) -> pd.Series:
    """
    Hull Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))

    wma1 = wma(series, half_length)
    wma2 = wma(series, period)

    raw_hma = 2 * wma1 - wma2
    return wma(raw_hma, sqrt_length)


def alma(series: pd.Series, period: int = 9, offset: float = 0.85, sigma: float = 6.0) -> pd.Series:
    """
    Arnaud Legoux Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")

    m = offset * (period - 1)
    s = period / sigma

    weights = np.exp(-((np.arange(period) - m) ** 2) / (2 * s ** 2))
    weights /= weights.sum()

    def apply_alma(x):
        if len(x) < period:
            return np.nan
        return np.dot(x, weights)

    return series.rolling(window=period, min_periods=period).apply(apply_alma, raw=True)


def kama(series: pd.Series, period: int = 10, fast_span: int = 2, slow_span: int = 30) -> pd.Series:
    """
    Kaufman's Adaptive Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")

    change = series.diff(period).abs()
    volatility = series.diff().abs().rolling(window=period, min_periods=period).sum()

    er = change / volatility.replace(0, np.nan)
    er = er.fillna(0)

    fast_alpha = 2.0 / (fast_span + 1)
    slow_alpha = 2.0 / (slow_span + 1)

    sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2

    kama_values = np.full_like(series, np.nan, dtype=float)

    # KAMA calculations need a loop as it depends on its own previous value
    first_valid = series.first_valid_index()
    if first_valid is None:
        return pd.Series(kama_values, index=series.index)

    first_valid_idx = series.index.get_loc(first_valid)
    start_idx = first_valid_idx + period

    if start_idx < len(series):
        # Initial KAMA value is the SMA of the first period
        kama_values[start_idx-1] = series.iloc[first_valid_idx:start_idx].mean()

        series_np = series.to_numpy()
        sc_np = sc.to_numpy()

        for i in range(start_idx, len(series)):
            if np.isnan(series_np[i]) or np.isnan(sc_np[i]) or np.isnan(kama_values[i-1]):
                kama_values[i] = series_np[i] if not np.isnan(series_np[i]) else kama_values[i-1]
            else:
                kama_values[i] = kama_values[i-1] + sc_np[i] * (series_np[i] - kama_values[i-1])

    return pd.Series(kama_values, index=series.index)


def t3(series: pd.Series, period: int = 5, vfactor: float = 0.7) -> pd.Series:
    """
    Tillson T3 Moving Average.
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")

    e1 = ema(series, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    e4 = ema(e3, period)
    e5 = ema(e4, period)
    e6 = ema(e5, period)

    v = vfactor
    c1 = -v**3
    c2 = 3*v**2 + 3*v**3
    c3 = -6*v**2 - 3*v - 3*v**3
    c4 = 1 + 3*v + v**3 + 3*v**2

    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3


def kairi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Kairi Relative Index (KRI).
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den küçük olamaz: {period}")
    
    ma = sma(series, period)
    return ((series - ma) / ma) * 100.0


def bb_width(series: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.Series:
    """
    Bollinger Bands Width.
    """
    upper, middle, lower = bollinger_bands(series, period, num_std)
    # middle 0 olma ihtimaline karsi
    return (upper - lower) / middle.replace(0, np.nan)


def gmma(series: pd.Series) -> dict[str, pd.Series]:
    """
    Guppy Multiple Moving Average (GMMA).
    Kısa ve uzun vadeli EMA grupları döndürür.
    
    Short: [3, 5, 8, 10, 12, 15]
    Long: [30, 35, 40, 45, 50, 60]
    """
    result = {}
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]
    
    for p in short_periods:
        result[f"short_{p}"] = ema(series, p)
        
    for p in long_periods:
        result[f"long_{p}"] = ema(series, p)
        
    return result


def most(
    close: pd.Series, 
    high: pd.Series, 
    low: pd.Series, 
    period: int = 3, 
    percent: float = 2.0
) -> tuple[pd.Series, pd.Series]:
    """
    Moving Average Trend (MOST) - Kivanc Ozbilgic tarafindan gelistirilmis
    trend takip eden hareketli ortalama indikatoru (ATR mantigi barindirmaz, 
    yuzdesel mesafe ile stop/trail kaydirir).
    Ancak ema ile hesaplanan klasik MOST surumudur: MOST = EMA(Close) +/- %Percent
    
    Returns:
        tuple: (most_line, ema_line)
    """
    if period < 1:
        raise ValueError(f"Periyot 1'den kucuk olamaz: {period}")

    ema_line = ema(close, period)
    
    most_line = np.full_like(close.values, np.nan, dtype=float)
    trend = 1
    
    close_np = close.values
    ema_np = ema_line.values
    pct = percent / 100.0
    
    first_valid = ema_line.first_valid_index()
    if first_valid is None:
        return pd.Series(most_line, index=close.index), ema_line
        
    start_idx = close.index.get_loc(first_valid)
    
    most_line[start_idx] = ema_np[start_idx] * (1 - pct) if trend == 1 else ema_np[start_idx] * (1 + pct)
    
    for i in range(start_idx + 1, len(close_np)):
        prev_most = most_line[i - 1]
        curr_ema = ema_np[i]
        
        if np.isnan(curr_ema) or np.isnan(prev_most):
             most_line[i] = prev_most if not np.isnan(prev_most) else curr_ema
             continue
             
        if trend == 1:
            if curr_ema < prev_most:
                trend = -1
                most_line[i] = curr_ema * (1 + pct)
            else:
                most_line[i] = max(prev_most, curr_ema * (1 - pct))
        else: # trend == -1
            if curr_ema > prev_most:
                trend = 1
                most_line[i] = curr_ema * (1 - pct)
            else:
                most_line[i] = min(prev_most, curr_ema * (1 + pct))
                
    return pd.Series(most_line, index=close.index), ema_line

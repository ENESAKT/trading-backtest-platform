import numpy as np
import pandas as pd
import pytest

from quant_engine.strategy.indicators import (
    sma, ema, wma, dema, tema, zlema, hma, alma, kama, t3,
    kairi, most, bb_width, gmma
)

@pytest.fixture
def sample_series():
    """1'den 20'ye kadar doğrusal artan örnek bir fiyat serisi"""
    return pd.Series(np.arange(1, 21, dtype=float))

@pytest.fixture
def volatile_series():
    """Volatiliteyi test etmek için dalgalı seri"""
    return pd.Series([10, 12, 11, 15, 14, 18, 17, 22, 20, 25, 23, 28, 27, 30])

def test_sma(sample_series):
    result = sma(sample_series, 3)
    assert len(result) == 20
    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == 2.0  # (1+2+3)/3 = 2.0
    assert result.iloc[19] == 19.0 # (18+19+20)/3 = 19.0

def test_ema(sample_series):
    result = ema(sample_series, 3)
    assert len(result) == 20
    # EMA hesaplaması ilk değeri kendisi alır
    assert result.iloc[0] == 1.0

def test_wma(sample_series):
    result = wma(sample_series, 3)
    assert len(result) == 20
    assert np.isnan(result.iloc[1])
    # WMA(1,2,3) = (1*1 + 2*2 + 3*3) / (1+2+3) = (1+4+9)/6 = 14/6 = 2.333...
    assert np.isclose(result.iloc[2], 14 / 6)

def test_dema(sample_series):
    result = dema(sample_series, 3)
    assert len(result) == 20
    assert not np.isnan(result.iloc[5])

def test_tema(sample_series):
    result = tema(sample_series, 3)
    assert len(result) == 20
    assert not np.isnan(result.iloc[5])

def test_zlema(sample_series):
    result = zlema(sample_series, 5)
    assert len(result) == 20
    # Lag for period 5 is 2. So the first two items should be NaN since shifted.
    assert np.isnan(result.iloc[1])
    assert not np.isnan(result.iloc[3])

def test_hma(sample_series):
    result = hma(sample_series, 4)
    assert len(result) == 20
    assert np.isnan(result.iloc[2])
    assert not np.isnan(result.iloc[5])

def test_alma(sample_series):
    result = alma(sample_series, 9)
    assert len(result) == 20
    assert np.isnan(result.iloc[7])
    assert not np.isnan(result.iloc[8])

def test_kama(volatile_series):
    result = kama(volatile_series, period=4, fast_span=2, slow_span=30)
    assert len(result) == 14
    assert np.isnan(result.iloc[2])
    # KAMA calculations start from period (index=3)
    assert not np.isnan(result.iloc[3])

def test_t3(sample_series):
    result = t3(sample_series, period=3, vfactor=0.7)
    assert len(result) == 20
    assert not np.isnan(result.iloc[5])

def test_invalid_period(sample_series):
    with pytest.raises(ValueError):
        wma(sample_series, 0)
    with pytest.raises(ValueError):
        zlema(sample_series, -1)
    with pytest.raises(ValueError):
        hma(sample_series, 0)
    with pytest.raises(ValueError):
        alma(sample_series, 0)
    with pytest.raises(ValueError):
        kama(sample_series, 0)
    with pytest.raises(ValueError):
        t3(sample_series, 0)

def test_insufficient_data():
    short_series = pd.Series([1.0, 2.0])
    result_alma = alma(short_series, 9)
    assert result_alma.isna().all()
    
    result_hma = hma(short_series, 10)
    assert result_hma.isna().all()

def test_kairi(sample_series):
    result = kairi(sample_series, 14)
    assert len(result) == 20
    assert np.isnan(result.iloc[12])
    assert not np.isnan(result.iloc[13])

def test_bb_width(sample_series):
    result = bb_width(sample_series, 5, 2.0)
    assert len(result) == 20
    assert np.isnan(result.iloc[3])
    assert not np.isnan(result.iloc[4])

def test_gmma(sample_series):
    result = gmma(sample_series)
    assert isinstance(result, dict)
    assert "short_3" in result
    assert "long_60" in result
    assert len(result["short_3"]) == 20
    assert len(result["long_60"]) == 20

def test_most(volatile_series):
    # MOST requires close, high, low but our implementation uses mainly close for logic
    # unless modified. 
    # Current most(): most(close, high, low, period, percent)
    # Actually the current signature is most(close, high, low, period, percent).
    # Since high and low are not heavily used in the core EMA logic it just passes through.
    
    high = volatile_series + 1
    low = volatile_series - 1
    
    most_line, ema_line = most(volatile_series, high, low, period=3, percent=2.0)
    
    assert len(most_line) == 14
    assert len(ema_line) == 14
    assert not np.isnan(most_line.iloc[-1])

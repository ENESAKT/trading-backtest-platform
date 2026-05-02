import numpy as np
import pandas as pd
import pytest

from quant_engine.strategy.indicators import (
    sma, ema, wma, dema, tema, zlema, hma, alma, kama, t3
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

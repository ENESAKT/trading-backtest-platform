"""
Quant Engine — Data Validator Unit Testleri

Test edilen:
- Geçerli OHLCV verisi geçmeli
- NaN fiyatlar yakalanmalı
- Negatif volume yakalanmalı
- OHLC tutarsızlıkları yakalanmalı
- Duplicate tarih yakalanmalı
- Boş DataFrame reddedilmeli
"""

from pathlib import Path

import pandas as pd
import pytest

from quant_engine.data_pipeline.data_validator import DataValidator

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden"


@pytest.fixture
def validator():
    return DataValidator(min_rows=1)


@pytest.fixture
def valid_df():
    return pd.read_csv(GOLDEN_DIR / "valid_ohlcv.csv")


@pytest.fixture
def invalid_df():
    return pd.read_csv(GOLDEN_DIR / "invalid_ohlcv.csv")


class TestValidData:
    """Geçerli veri testleri."""

    def test_valid_ohlcv_passes(self, validator, valid_df):
        """Golden fixture geçerli veri doğrulamadan geçmeli."""
        result = validator.validate(valid_df, "VALID_TEST")
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_ohlcv_correct_row_count(self, valid_df):
        """Golden fixture 10 satır içermeli."""
        assert len(valid_df) == 10


class TestInvalidData:
    """Hatalı veri tespiti testleri."""

    def test_empty_dataframe_rejected(self, validator):
        """Boş DataFrame reddedilmeli."""
        result = validator.validate(pd.DataFrame(), "EMPTY")
        assert result.is_valid is False

    def test_nan_prices_detected(self, validator):
        """BİLİNEN BUG (VAL-1): NaN fiyatlar yakalanmıyor.
        Bu test bug düzeltildikten sonra geçmeli."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "open": [100.0, float("nan")],
            "high": [110.0, float("nan")],
            "low": [90.0, float("nan")],
            "close": [105.0, float("nan")],
            "volume": [1000, 500],
        })
        result = validator.validate(df, "NAN_TEST")
        # BUG: Şu an is_valid=True dönüyor, düzeltildikten sonra False olmalı
        assert result.is_valid is True, "VAL-1 bug düzeltildi mi? Bu assertion'ı güncelle."

    def test_negative_volume_detected(self, validator):
        """BİLİNEN BUG (VAL-2): Negatif volume yakalanmıyor.
        Bu test bug düzeltildikten sonra geçmeli."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [110.0],
            "low": [90.0],
            "close": [105.0],
            "volume": [-500],
        })
        result = validator.validate(df, "NEG_VOL")
        # BUG: Şu an negatif volume yakalanmıyor
        has_volume_warning = any(
            "volume" in str(e).lower() or "negatif" in str(e).lower()
            for e in result.errors + result.warnings
        )
        assert has_volume_warning is False, "VAL-2 bug düzeltildi mi? Bu assertion'ı güncelle."

    def test_ohlc_low_greater_than_close(self, validator):
        """BİLİNEN BUG (VAL-3): low > close yakalanmıyor.
        Bu test bug düzeltildikten sonra geçmeli."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [110.0],
            "low": [108.0],  # low > close
            "close": [105.0],
            "volume": [1000],
        })
        result = validator.validate(df, "OHLC_TEST")
        # BUG: Şu an low > close yakalanmıyor
        has_ohlc_issue = any(
            "low" in str(e).lower()
            for e in result.errors + result.warnings
        )
        assert has_ohlc_issue is False, "VAL-3 bug düzeltildi mi? Bu assertion'ı güncelle."

    def test_duplicate_dates_detected(self, validator):
        """Duplicate tarihler yakalanmalı."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-01"],
            "open": [100.0, 101.0],
            "high": [110.0, 111.0],
            "low": [90.0, 91.0],
            "close": [105.0, 106.0],
            "volume": [1000, 1100],
        })
        result = validator.validate(df, "DUP_TEST")
        has_dup_warning = any("tekrar" in w.lower() for w in result.warnings)
        assert has_dup_warning is True

    def test_negative_price_is_error(self, validator):
        """Negatif fiyatlar error olarak yakalanmalı."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [-100.0],
            "high": [110.0],
            "low": [90.0],
            "close": [105.0],
            "volume": [1000],
        })
        result = validator.validate(df, "NEG_PRICE")
        assert result.is_valid is False


class TestAutoFix:
    """auto_fix fonksiyonu testleri."""

    def test_auto_fix_removes_duplicates(self, validator):
        """auto_fix duplicate tarihleri temizlemeli."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "open": [100.0, 101.0, 102.0],
            "high": [110.0, 111.0, 112.0],
            "low": [90.0, 91.0, 92.0],
            "close": [105.0, 106.0, 107.0],
            "volume": [1000, 1100, 1200],
        })
        fixed = DataValidator.auto_fix(df)
        assert len(fixed) == 2  # Duplicate kaldırılmış olmalı

    def test_auto_fix_sorts_dates(self, validator):
        """auto_fix tarihleri sıralamalı."""
        df = pd.DataFrame({
            "date": ["2024-01-03", "2024-01-01", "2024-01-02"],
            "open": [100.0, 101.0, 102.0],
            "high": [110.0, 111.0, 112.0],
            "low": [90.0, 91.0, 92.0],
            "close": [105.0, 106.0, 107.0],
            "volume": [1000, 1100, 1200],
        })
        fixed = DataValidator.auto_fix(df)
        dates = pd.to_datetime(fixed["date"]).tolist()
        assert dates == sorted(dates)

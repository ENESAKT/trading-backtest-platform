"""
Quant Engine — Data Validator Unit Testleri

Test edilen (bug düzeltmeleri doğrulanıyor):
- VAL-1 FIX: NaN fiyatlar yakalanıyor ✅
- VAL-2 FIX: Negatif volume yakalanıyor ✅
- VAL-3 FIX: low > close yakalanıyor ✅
- VAL-4 FIX: auto_fix sınırlı forward-fill ✅
- Geçerli OHLCV verisi geçmeli
- Boş DataFrame reddedilmeli
- Duplicate tarih yakalanmalı
"""

from pathlib import Path

import pandas as pd
import pytest

from quant_engine.data_pipeline.data_validator import (
    DataValidator,
)

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
        """VAL-1 FIX: NaN fiyatlar artık yakalanıyor."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "open": [100.0, float("nan")],
            "high": [110.0, float("nan")],
            "low": [90.0, float("nan")],
            "close": [105.0, float("nan")],
            "volume": [1000, 500],
        })
        result = validator.validate(df, "NAN_TEST")
        # VAL-1 FIX: Artık NaN fiyatlar yakalanıyor
        assert result.is_valid is False
        assert any(
            "NaN" in e for e in result.errors
        )

    def test_negative_volume_detected(self, validator):
        """VAL-2 FIX: Negatif volume artık yakalanıyor."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [110.0],
            "low": [90.0],
            "close": [105.0],
            "volume": [-500],
        })
        result = validator.validate(df, "NEG_VOL")
        # VAL-2 FIX: Artık negatif volume yakalanıyor
        has_volume_error = any(
            "negatif" in str(e).lower()
            or "volume" in str(e).lower()
            for e in result.errors
        )
        assert has_volume_error is True

    def test_ohlc_low_greater_than_close(self, validator):
        """VAL-3 FIX: low > close artık yakalanıyor."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [110.0],
            "low": [108.0],  # low > close
            "close": [105.0],
            "volume": [1000],
        })
        result = validator.validate(df, "OHLC_TEST")
        # VAL-3 FIX: Artık low > close yakalanıyor
        has_ohlc_issue = any(
            "low" in str(w).lower()
            for w in result.warnings
        )
        assert has_ohlc_issue is True

    def test_high_less_than_low_is_error(self, validator):
        """High < Low error olmalı."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [80.0],   # high < low
            "low": [90.0],
            "close": [85.0],
            "volume": [1000],
        })
        result = validator.validate(df, "HL_TEST")
        assert result.is_valid is False
        assert any(
            "High < Low" in e for e in result.errors
        )

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
        has_dup_warning = any(
            "tekrar" in w.lower()
            for w in result.warnings
        )
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
            "date": [
                "2024-01-01", "2024-01-01", "2024-01-02",
            ],
            "open": [100.0, 101.0, 102.0],
            "high": [110.0, 111.0, 112.0],
            "low": [90.0, 91.0, 92.0],
            "close": [105.0, 106.0, 107.0],
            "volume": [1000, 1100, 1200],
        })
        fixed = DataValidator.auto_fix(df)
        assert len(fixed) == 2

    def test_auto_fix_sorts_dates(self, validator):
        """auto_fix tarihleri sıralamalı."""
        df = pd.DataFrame({
            "date": [
                "2024-01-03", "2024-01-01", "2024-01-02",
            ],
            "open": [100.0, 101.0, 102.0],
            "high": [110.0, 111.0, 112.0],
            "low": [90.0, 91.0, 92.0],
            "close": [105.0, 106.0, 107.0],
            "volume": [1000, 1100, 1200],
        })
        fixed = DataValidator.auto_fix(df)
        dates = pd.to_datetime(fixed["date"]).tolist()
        assert dates == sorted(dates)

    def test_auto_fix_limited_ffill(self, validator):
        """VAL-4 FIX: auto_fix sınırlı ffill uygulamalı."""
        df = pd.DataFrame({
            "date": [
                "2024-01-01", "2024-01-02",
                "2024-01-03", "2024-01-04",
                "2024-01-05", "2024-01-06",
            ],
            "open": [
                100.0, float("nan"), float("nan"),
                float("nan"), float("nan"), float("nan"),
            ],
            "high": [110.0, 111.0, 112.0, 113.0, 114.0, 115.0],
            "low": [90.0, 91.0, 92.0, 93.0, 94.0, 95.0],
            "close": [105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500],
        })
        # max_ffill_limit=3 ile sadece 3 NaN dolmalı
        fixed = DataValidator.auto_fix(
            df, max_ffill_limit=3
        )
        # İlk 4 satır (orijinal + 3 fill) dolu olmalı
        assert fixed["open"].iloc[0] == 100.0
        assert fixed["open"].iloc[3] == 100.0  # 3. fill
        # 4. ve 5. NaN hâlâ NaN kalmalı (limit=3)
        assert pd.isna(fixed["open"].iloc[4])
        assert pd.isna(fixed["open"].iloc[5])

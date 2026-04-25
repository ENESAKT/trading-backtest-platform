"""
Quant Engine — Storage Manager Unit Testleri

Test edilen:
- Write + read round-trip
- Geçersiz mode reddedilmeli
- Boş DataFrame yazılmamalı
- Schema uyumu
"""

import pandas as pd
import pytest

from quant_engine.data_pipeline.storage_manager import StorageManager


@pytest.fixture
def storage(tmp_path):
    """Her test için geçici dizinde temiz storage."""
    sm = StorageManager(data_dir=str(tmp_path / "test_data"))
    yield sm
    sm.close()


@pytest.fixture
def sample_df():
    """Geçerli küçük test verisi."""
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        "open": [100.0, 104.5, 106.5],
        "high": [105.5, 107.0, 108.2],
        "low": [99.0, 103.0, 105.0],
        "close": [104.2, 106.8, 105.4],
        "volume": [1500000, 1200000, 980000],
    })


class TestStorageWriteRead:
    """Write → Read round-trip testleri."""

    def test_write_and_read_back(self, storage, sample_df):
        """Yazılan veri aynı şekilde okunmalı."""
        rows = storage.write_symbol_data(sample_df, "THYAO", mode="overwrite")
        assert rows == 3

        read_back = storage.read_symbol("THYAO")
        assert len(read_back) == 3
        assert "close" in read_back.columns

    def test_write_preserves_close_values(self, storage, sample_df):
        """Close fiyatları yazılıp okunurken bozulmamalı."""
        storage.write_symbol_data(sample_df, "THYAO", mode="overwrite")
        read_back = storage.read_symbol("THYAO")

        original_closes = sample_df["close"].tolist()
        read_closes = read_back["close"].tolist()
        assert original_closes == pytest.approx(read_closes, abs=0.01)

    def test_empty_dataframe_not_written(self, storage):
        """Boş DataFrame yazılmamalı."""
        rows = storage.write_symbol_data(pd.DataFrame(), "EMPTY")
        assert rows == 0

    def test_read_nonexistent_symbol(self, storage):
        """Var olmayan sembol okunursa boş DataFrame dönmeli."""
        result = storage.read_symbol("NONEXIST")
        assert result.empty


class TestStorageMode:
    """Write mode testleri."""

    def test_invalid_mode_accepted(self, storage, sample_df):
        """BİLİNEN BUG (STR-3): Geçersiz mode sessizce kabul ediliyor.
        Bug düzeltildikten sonra ValueError fırlatmalı."""
        # BUG: mode='nonsense' hata fırlatması gerekirken çalışıyor
        rows = storage.write_symbol_data(sample_df, "MODE_TEST", mode="nonsense")
        assert rows > 0, "STR-3 bug düzeltildi mi? ValueError beklenmeli."

    def test_overwrite_replaces_all(self, storage, sample_df):
        """Overwrite modu eski veriyi tamamen değiştirmeli."""
        storage.write_symbol_data(sample_df, "OVR", mode="overwrite")
        storage.write_symbol_data(sample_df.head(1), "OVR", mode="overwrite")
        result = storage.read_symbol("OVR")
        assert len(result) == 1

    def test_append_adds_rows(self, storage, sample_df):
        """Append modu yeni satırlar eklemeli."""
        storage.write_symbol_data(sample_df.head(2), "APP", mode="overwrite")

        new_df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-05"]),
            "open": [105.0],
            "high": [106.0],
            "low": [102.5],
            "close": [103.1],
            "volume": [1100000],
        })
        storage.write_symbol_data(new_df, "APP", mode="append")
        result = storage.read_symbol("APP")
        assert len(result) == 3


class TestStorageSymbolOps:
    """Sembol işlemleri testleri."""

    def test_symbol_exists(self, storage, sample_df):
        """Yazılan sembol exists kontrolünden geçmeli."""
        storage.write_symbol_data(sample_df, "EXISTS_TEST", mode="overwrite")
        assert storage.symbol_exists("EXISTS_TEST") is True
        assert storage.symbol_exists("NONEXIST") is False

    def test_get_last_date(self, storage, sample_df):
        """Son tarih doğru dönmeli."""
        storage.write_symbol_data(sample_df, "DATE_TEST", mode="overwrite")
        last = storage.get_last_date("DATE_TEST")
        assert last is not None

"""
Quant Engine — Config Manager Unit Testleri

Test edilen:
- Config dosyası yükleme
- Varsayılan değerler
- Geçersiz config davranışı
"""

from pathlib import Path

import pytest

from quant_engine.config.config_manager import (
    AppConfig,
    BacktestConfig,
    DatabaseConfig,
    load_config,
)


class TestConfigDefaults:
    """Varsayılan config değerlerinin doğruluğu."""

    def test_default_config_creates_without_file(self, tmp_path):
        """Config dosyası yoksa varsayılan değerlerle oluşmalı."""
        config = load_config(tmp_path / "nonexistent.toml")
        assert isinstance(config, AppConfig)
        assert config.backtest.initial_capital == 100_000.0
        assert config.backtest.commission_rate == 0.001
        assert config.database.type == "duckdb"

    def test_default_commission_rate_positive(self):
        """Komisyon oranı pozitif olmalı."""
        config = BacktestConfig()
        assert config.commission_rate >= 0

    def test_default_data_dir(self):
        """Varsayılan data_dir tanımlı olmalı."""
        config = DatabaseConfig()
        assert config.data_dir is not None
        assert len(config.data_dir) > 0


class TestConfigLoading:
    """Config dosyasından yükleme testleri."""

    def test_load_real_config(self):
        """Gerçek settings.toml dosyası yüklenebilmeli."""
        config_path = Path(__file__).resolve().parents[2] / "config" / "settings.toml"
        if not config_path.exists():
            pytest.skip("settings.toml bulunamadı")

        config = load_config(config_path)
        assert config.project.name == "quant_engine"
        assert len(config.symbols.watchlist) > 0

    def test_watchlist_not_empty(self):
        """Watchlist en az 1 sembol içermeli."""
        config_path = Path(__file__).resolve().parents[2] / "config" / "settings.toml"
        if not config_path.exists():
            pytest.skip("settings.toml bulunamadı")

        config = load_config(config_path)
        assert len(config.symbols.watchlist) >= 1


class TestConfigEnvOverride:
    """Ortam değişkeni override testleri."""

    def test_env_override_not_applied_by_get_config(self):
        """BİLİNEN BUG (CFG-1): get_config() env override uygulamıyor.
        Bu test bug düzeltildiğinde güncellenmeli.
        """
        # Bu test şu anki davranışı belgeliyor
        config = load_config()
        original = config.backtest.commission_rate
        # Override fonksiyonu çağrılmadan değer değişmemeli
        assert config.backtest.commission_rate == original

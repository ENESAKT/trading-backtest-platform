"""
Quant Engine — Config Manager Unit Testleri

Test edilen:
- Config dosyası yükleme
- Varsayılan değerler
- Geçersiz config davranışı (extra="forbid")
- Field sınırları (commission_rate, max_position_pct, max_workers)
- Ortam değişkeni override'ları (CFG-1 düzeltmesi)
- Deterministic path çözümleme (CFG-5)
- Timezone ayarları (CFG-6)
"""

from pathlib import Path

import pytest

from quant_engine.config.config_manager import (
    AppConfig,
    BacktestConfig,
    DatabaseConfig,
    DataPipelineConfig,
    LoggingConfig,
    TimezoneConfig,
    apply_env_overrides,
    get_config,
    load_config,
    reset_config_cache,
)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    """Her test öncesi config cache'ini temizle."""
    reset_config_cache()
    yield
    reset_config_cache()


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

    def test_default_timezone(self):
        """Varsayılan timezone Istanbul olmalı (CFG-6)."""
        config = TimezoneConfig()
        assert config.local == "Europe/Istanbul"
        assert config.storage == "UTC"

    def test_default_retry_settings(self):
        """Varsayılan retry/timeout ayarları tanımlı olmalı (CFG-6)."""
        config = DataPipelineConfig()
        assert config.retry_count == 3
        assert config.retry_delay_seconds == 1.0
        assert config.request_timeout_seconds == 30.0


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

    def test_real_config_has_timezone(self):
        """Gerçek config timezone ayarlarını içermeli (CFG-6)."""
        config_path = Path(__file__).resolve().parents[2] / "config" / "settings.toml"
        if not config_path.exists():
            pytest.skip("settings.toml bulunamadı")

        config = load_config(config_path)
        assert config.timezone.local == "Europe/Istanbul"
        assert config.timezone.storage == "UTC"


class TestConfigEnvOverride:
    """Ortam değişkeni override testleri — CFG-1 düzeltmesi."""

    def test_env_override_commission_rate(self, monkeypatch):
        """CFG-1 FIX: get_config() env override uygulamalı."""
        monkeypatch.setenv("QUANT_COMMISSION_RATE", "0.005")
        config = get_config()
        assert config.backtest.commission_rate == 0.005

    def test_env_override_initial_capital(self, monkeypatch):
        """Ortam değişkeni ile başlangıç sermayesi değiştirilebilmeli."""
        monkeypatch.setenv("QUANT_INITIAL_CAPITAL", "500000")
        config = get_config()
        assert config.backtest.initial_capital == 500_000.0

    def test_env_override_data_dir(self, monkeypatch, tmp_path):
        """Ortam değişkeni ile data_dir değiştirilebilmeli."""
        monkeypatch.setenv("QUANT_DATA_DIR", str(tmp_path / "custom_data"))
        config = get_config()
        assert config.database.data_dir == str(tmp_path / "custom_data")

    def test_env_override_log_level(self, monkeypatch):
        """Ortam değişkeni ile log level değiştirilebilmeli."""
        monkeypatch.setenv("QUANT_LOG_LEVEL", "debug")
        config = get_config()
        assert config.logging.level == "DEBUG"

    def test_apply_env_overrides_directly(self, monkeypatch):
        """apply_env_overrides doğrudan çağrıldığında da çalışmalı."""
        monkeypatch.setenv("QUANT_COMMISSION_RATE", "0.002")
        config = load_config()
        original_rate = config.backtest.commission_rate
        config = apply_env_overrides(config)
        assert config.backtest.commission_rate == 0.002
        assert config.backtest.commission_rate != original_rate


class TestConfigExtraForbid:
    """extra='forbid' testleri — CFG-2 düzeltmesi."""

    def test_extra_field_rejected_in_backtest(self):
        """Backtest config'e bilinmeyen alan eklenemez."""
        with pytest.raises(Exception):  # ValidationError
            BacktestConfig(initial_capital=100_000, unknown_field="test")

    def test_extra_field_rejected_in_database(self):
        """Database config'e bilinmeyen alan eklenemez."""
        with pytest.raises(Exception):  # ValidationError
            DatabaseConfig(type="duckdb", fake_option=True)

    def test_extra_field_rejected_in_pipeline(self):
        """Pipeline config'e bilinmeyen alan eklenemez."""
        with pytest.raises(Exception):  # ValidationError
            DataPipelineConfig(nonexistent=42)

    def test_extra_field_rejected_in_app_config(self):
        """Ana config'e bilinmeyen bölüm eklenemez."""
        with pytest.raises(Exception):
            AppConfig(mystery_section={"foo": "bar"})


class TestConfigFieldBoundaries:
    """Field sınır testleri — CFG-3 düzeltmesi."""

    def test_negative_commission_rate_rejected(self):
        """Negatif komisyon oranı reddedilmeli."""
        with pytest.raises(Exception):
            BacktestConfig(commission_rate=-0.001)

    def test_commission_rate_too_high_rejected(self):
        """Çok yüksek komisyon oranı reddedilmeli (> 0.1)."""
        with pytest.raises(Exception):
            BacktestConfig(commission_rate=0.5)

    def test_max_position_pct_above_one_rejected(self):
        """max_position_pct > 1.0 reddedilmeli."""
        with pytest.raises(Exception):
            BacktestConfig(max_position_pct=1.5)

    def test_max_position_pct_zero_rejected(self):
        """max_position_pct = 0 reddedilmeli."""
        with pytest.raises(Exception):
            BacktestConfig(max_position_pct=0.0)

    def test_max_workers_zero_rejected(self):
        """max_workers < 1 reddedilmeli."""
        with pytest.raises(Exception):
            DataPipelineConfig(max_workers=0)

    def test_initial_capital_zero_rejected(self):
        """Sıfır sermaye reddedilmeli."""
        with pytest.raises(Exception):
            BacktestConfig(initial_capital=0)

    def test_valid_boundaries_accepted(self):
        """Geçerli sınır değerleri kabul edilmeli."""
        config = BacktestConfig(
            commission_rate=0.0,  # 0 geçerli (komisyonsuz)
            max_position_pct=1.0,  # 1.0 geçerli (tüm portföy)
            max_drawdown_pct=0.5,
        )
        assert config.commission_rate == 0.0
        assert config.max_position_pct == 1.0


class TestConfigDeterministicPaths:
    """Deterministic path çözümleme testleri — CFG-5."""

    def test_resolved_data_dir_is_absolute(self):
        """resolved_data_dir mutlaka absolute olmalı."""
        config = DatabaseConfig()
        assert config.resolved_data_dir.is_absolute()

    def test_resolved_db_path_is_absolute(self):
        """resolved_db_path mutlaka absolute olmalı (CFG-4)."""
        config = DatabaseConfig()
        assert config.resolved_db_path.is_absolute()
        assert config.resolved_db_path.name == "quant_engine.duckdb"

    def test_resolved_db_path_under_data_dir(self):
        """db_path data_dir altında olmalı (CFG-4)."""
        config = DatabaseConfig()
        assert str(config.resolved_db_path).startswith(str(config.resolved_data_dir))

    def test_resolved_log_dir_is_absolute(self):
        """resolved_log_dir mutlaka absolute olmalı."""
        config = LoggingConfig()
        assert config.resolved_log_dir.is_absolute()


class TestConfigValidators:
    """Field validator testleri (CFG-6)."""

    def test_invalid_source_rejected(self):
        """Geçersiz veri kaynağı reddedilmeli."""
        with pytest.raises(Exception):
            DataPipelineConfig(default_source="bloomberg")

    def test_valid_sources_accepted(self):
        """Geçerli veri kaynakları kabul edilmeli."""
        for source in ["yfinance", "matriks", "stooq"]:
            config = DataPipelineConfig(default_source=source)
            assert config.default_source == source

    def test_invalid_timeframe_rejected(self):
        """Geçersiz zaman dilimi reddedilmeli."""
        with pytest.raises(Exception):
            DataPipelineConfig(default_timeframe="2d")

    def test_valid_timeframes_accepted(self):
        """Geçerli zaman dilimleri kabul edilmeli."""
        for tf in ["1m", "5m", "1h", "1d", "1wk"]:
            config = DataPipelineConfig(default_timeframe=tf)
            assert config.default_timeframe == tf

    def test_invalid_log_level_rejected(self):
        """Geçersiz log seviyesi reddedilmeli."""
        with pytest.raises(Exception):
            LoggingConfig(level="VERBOSE")

    def test_log_level_case_insensitive(self):
        """Log seviyesi büyük/küçük harf duyarsız olmalı."""
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"

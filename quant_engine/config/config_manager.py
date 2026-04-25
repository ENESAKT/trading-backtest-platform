"""
Quant Engine — Merkezi Konfigürasyon Yöneticisi (Pydantic + TOML)

Tüm modüller bu dosyadaki modelleri kullanarak ayarlara erişir.
TOML dosyasından okunan değerler Pydantic ile tip kontrolünden geçirilir.

Düzeltilen bug'lar:
    CFG-1: get_config() artık apply_env_overrides() çağırıyor
    CFG-2: Tüm modellere extra="forbid" eklendi
    CFG-3: Field sınırları eklendi (commission_rate >= 0, max_position_pct 0-1, max_workers >= 1)
    CFG-4: db_path kaldırıldı — data_dir'den türetiliyor
    CFG-5: data_dir proje köküne göre deterministic resolve
    CFG-6: timezone, source, timeframe, retry, timeout ayarları eklendi
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11 fallback

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Proje Kökünü Belirle (deterministic — CFG-5)
# ---------------------------------------------------------------------------

# Proje kökü: config_manager.py → config/ → quant_engine/ → PROJE KÖKÜ
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_path(raw_path: str) -> Path:
    """Göreli yolu proje köküne göre çözümle (CFG-5)."""
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


# ---------------------------------------------------------------------------
# Konfigürasyon Modelleri (CFG-2: extra="forbid" eklendi)
# ---------------------------------------------------------------------------

class DatabaseConfig(BaseModel):
    """Veritabanı ayarları — DuckDB + Parquet"""
    model_config = ConfigDict(extra="forbid")

    type: str = "duckdb"
    data_dir: str = "./data"
    # CFG-4: db_path kaldırıldı — data_dir'den türetilecek

    @property
    def resolved_data_dir(self) -> Path:
        """Proje köküne göre çözümlenmiş data_dir (CFG-5)."""
        return _resolve_path(self.data_dir)

    @property
    def resolved_db_path(self) -> Path:
        """db_path artık data_dir'den türetiliyor (CFG-4)."""
        return self.resolved_data_dir / "quant_engine.duckdb"


class DataPipelineConfig(BaseModel):
    """Veri çekme pipeline ayarları"""
    model_config = ConfigDict(extra="forbid")

    default_source: str = "yfinance"
    ticker_suffix: str = ".IS"
    enable_delta_fetch: bool = True
    default_start_date: str = "2015-01-01"
    max_workers: int = Field(default=4, ge=1, description="Paralel iş parçacığı sayısı (CFG-3)")

    # CFG-6: Yeni ayarlar
    default_timeframe: str = Field(
        default="1d", description="Varsayılan zaman dilimi"
    )
    retry_count: int = Field(
        default=3, ge=0,
        description="Başarısız isteklerde tekrar deneme sayısı",
    )
    retry_delay_seconds: float = Field(
        default=1.0, ge=0.0,
        description="Tekrar denemeler arası bekleme",
    )
    request_timeout_seconds: float = Field(
        default=30.0, gt=0.0,
        description="HTTP istek zaman aşımı",
    )

    @field_validator("default_source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"yfinance", "matriks", "stooq", "bist_verda", "tcmb_evds"}
        if v not in allowed:
            raise ValueError(f"Geçersiz kaynak: '{v}'. İzin verilenler: {allowed}")
        return v

    @field_validator("default_timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        allowed = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"}
        if v not in allowed:
            raise ValueError(f"Geçersiz zaman dilimi: '{v}'. İzin verilenler: {allowed}")
        return v


class BacktestConfig(BaseModel):
    """Backtest motoru ayarları"""
    model_config = ConfigDict(extra="forbid")

    initial_capital: float = Field(
        default=100_000.0, gt=0.0,
        description="Başlangıç sermayesi (TRY)"
    )
    commission_rate: float = Field(
        default=0.001, ge=0.0, le=0.1,
        description="Komisyon oranı — 0 ile 0.1 arası (CFG-3)"
    )
    slippage_bps: int = Field(
        default=5, ge=0,
        description="Kayma (slippage) — baz puan"
    )
    default_timeframe: str = "1d"
    max_position_pct: float = Field(
        default=0.20, gt=0.0, le=1.0,
        description="Maksimum pozisyon yüzdesi — 0-1 arası (CFG-3)"
    )
    max_drawdown_pct: float = Field(
        default=0.25, gt=0.0, le=1.0,
        description="Maksimum düşüş yüzdesi — 0-1 arası"
    )


class SymbolsConfig(BaseModel):
    """Takip edilen semboller"""
    model_config = ConfigDict(extra="forbid")

    watchlist: list[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    """Loglama ayarları"""
    model_config = ConfigDict(extra="forbid")

    level: str = "INFO"
    log_dir: str = "./logs"
    rotation: str = "10 MB"

    @property
    def resolved_log_dir(self) -> Path:
        """Proje köküne göre çözümlenmiş log_dir (CFG-5)."""
        return _resolve_path(self.log_dir)

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "TRACE", "SUCCESS"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Geçersiz log seviyesi: '{v}'. İzin verilenler: {allowed}")
        return v_upper


class PerformanceConfig(BaseModel):
    """Performans optimizasyon ayarları"""
    model_config = ConfigDict(extra="forbid")

    polars_max_threads: int = Field(default=8, ge=1)
    numba_parallel: bool = True


class ProjectConfig(BaseModel):
    """Proje metadata"""
    model_config = ConfigDict(extra="forbid")

    name: str = "quant_engine"
    version: str = "0.1.0"
    description: str = ""


class TimezoneConfig(BaseModel):
    """Timezone ayarları (CFG-6)"""
    model_config = ConfigDict(extra="forbid")

    local: str = Field(default="Europe/Istanbul", description="Yerel saat dilimi")
    storage: str = Field(default="UTC", description="Depolama saat dilimi")


class AppConfig(BaseModel):
    """Ana konfigürasyon — tüm alt ayarları barındırır"""
    model_config = ConfigDict(extra="forbid")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data_pipeline: DataPipelineConfig = Field(default_factory=DataPipelineConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    symbols: SymbolsConfig = Field(default_factory=SymbolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    timezone: TimezoneConfig = Field(default_factory=TimezoneConfig)


# ---------------------------------------------------------------------------
# Konfigürasyon Yükleme
# ---------------------------------------------------------------------------

def _find_config_path() -> Path:
    """Konfigürasyon dosyasını bul — proje kökünden yukarı doğru arar."""
    search_paths = [
        PROJECT_ROOT / "config" / "settings.toml",
        Path.cwd() / "config" / "settings.toml",
        Path.cwd() / "settings.toml",
    ]
    for path in search_paths:
        if path.exists():
            return path

    # Bulunamazsa varsayılan ayarlarla devam et
    return PROJECT_ROOT / "config" / "settings.toml"


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """
    TOML dosyasından konfigürasyonu yükle ve doğrula.

    Args:
        config_path: TOML dosya yolu. None ise otomatik arar.

    Returns:
        AppConfig: Doğrulanmış konfigürasyon nesnesi.
    """
    if config_path is None:
        config_path = _find_config_path()

    config_path = Path(config_path)

    if not config_path.exists():
        # Dosya yoksa varsayılan ayarlarla döndür
        return AppConfig()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return AppConfig(**raw)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """
    Singleton config erişimi — uygulama boyunca tek bir config nesnesi kullanılır.
    İlk çağrıda yükler, env override uygular, sonraki çağrılarda cache'ten döndürür.

    CFG-1 FIX: Artık apply_env_overrides() çağrılıyor.
    """
    config = load_config()
    config = apply_env_overrides(config)
    return config


def reset_config_cache() -> None:
    """Config cache'ini temizle — testlerde kullanım için."""
    get_config.cache_clear()


# ---------------------------------------------------------------------------
# Ortam Değişkeni Override'ları
# ---------------------------------------------------------------------------

def apply_env_overrides(config: AppConfig) -> AppConfig:
    """
    Ortam değişkenleri ile config değerlerini override et.
    Örn: QUANT_BACKTEST_COMMISSION_RATE=0.002

    Not: Pydantic modelleri frozen değil, doğrudan atama yapılabiliyor.
    Ancak extra="forbid" sayesinde geçersiz alan atanamaz.
    """
    prefix = "QUANT_"

    if val := os.environ.get(f"{prefix}DATA_DIR"):
        config.database.data_dir = val
    if val := os.environ.get(f"{prefix}INITIAL_CAPITAL"):
        config.backtest.initial_capital = float(val)
    if val := os.environ.get(f"{prefix}COMMISSION_RATE"):
        config.backtest.commission_rate = float(val)
    if val := os.environ.get(f"{prefix}LOG_LEVEL"):
        config.logging.level = val.upper()
    if val := os.environ.get(f"{prefix}TIMEZONE"):
        config.timezone.local = val

    return config

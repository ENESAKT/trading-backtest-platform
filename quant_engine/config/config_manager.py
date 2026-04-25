"""
Quant Engine — Merkezi Konfigürasyon Yöneticisi (Pydantic + TOML)

Tüm modüller bu dosyadaki modelleri kullanarak ayarlara erişir.
TOML dosyasından okunan değerler Pydantic ile tip kontrolünden geçirilir.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11 fallback

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Konfigürasyon Modelleri
# ---------------------------------------------------------------------------

class DatabaseConfig(BaseModel):
    """Veritabanı ayarları — DuckDB + Parquet"""
    type: str = "duckdb"
    data_dir: str = "./data"
    db_path: str = "./data/quant_engine.duckdb"


class DataPipelineConfig(BaseModel):
    """Veri çekme pipeline ayarları"""
    default_source: str = "yfinance"
    ticker_suffix: str = ".IS"
    enable_delta_fetch: bool = True
    default_start_date: str = "2015-01-01"
    max_workers: int = 4


class BacktestConfig(BaseModel):
    """Backtest motoru ayarları"""
    initial_capital: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: int = 5
    default_timeframe: str = "1d"
    max_position_pct: float = 0.20
    max_drawdown_pct: float = 0.25


class SymbolsConfig(BaseModel):
    """Takip edilen semboller"""
    watchlist: list[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    """Loglama ayarları"""
    level: str = "INFO"
    log_dir: str = "./logs"
    rotation: str = "10 MB"


class PerformanceConfig(BaseModel):
    """Performans optimizasyon ayarları"""
    polars_max_threads: int = 8
    numba_parallel: bool = True


class ProjectConfig(BaseModel):
    """Proje metadata"""
    name: str = "quant_engine"
    version: str = "0.1.0"
    description: str = ""


class AppConfig(BaseModel):
    """Ana konfigürasyon — tüm alt ayarları barındırır"""
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data_pipeline: DataPipelineConfig = Field(default_factory=DataPipelineConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    symbols: SymbolsConfig = Field(default_factory=SymbolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)


# ---------------------------------------------------------------------------
# Konfigürasyon Yükleme
# ---------------------------------------------------------------------------

def _find_config_path() -> Path:
    """Konfigürasyon dosyasını bul — proje kökünden yukarı doğru arar."""
    search_paths = [
        Path.cwd() / "config" / "settings.toml",
        Path.cwd() / "settings.toml",
        Path(__file__).resolve().parent.parent.parent / "config" / "settings.toml",
    ]
    for path in search_paths:
        if path.exists():
            return path

    # Bulunamazsa varsayılan ayarlarla devam et
    return Path("config/settings.toml")


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
    İlk çağrıda yükler, sonraki çağrılarda cache'ten döndürür.
    """
    return load_config()


# ---------------------------------------------------------------------------
# Ortam Değişkeni Override'ları
# ---------------------------------------------------------------------------

def apply_env_overrides(config: AppConfig) -> AppConfig:
    """
    Ortam değişkenleri ile config değerlerini override et.
    Örn: QUANT_BACKTEST_COMMISSION_RATE=0.002
    """
    prefix = "QUANT_"
    
    if val := os.environ.get(f"{prefix}DATA_DIR"):
        config.database.data_dir = val
    if val := os.environ.get(f"{prefix}INITIAL_CAPITAL"):
        config.backtest.initial_capital = float(val)
    if val := os.environ.get(f"{prefix}COMMISSION_RATE"):
        config.backtest.commission_rate = float(val)
    if val := os.environ.get(f"{prefix}LOG_LEVEL"):
        config.logging.level = val
    
    return config

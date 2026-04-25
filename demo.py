#!/usr/bin/env python3
"""
Quant Engine — Demo & Test Betiği

Bu betik tüm pipeline'ı uçtan uca test eder:
1. Bir hissenin verisini Yahoo Finance'tan çeker
2. Veri kalitesini doğrular
3. DuckDB/Parquet'e yazar
4. Geri okur ve istatistikleri gösterir

Kullanım:
    # Sanal ortamı aktive et
    source .venv/bin/activate
    
    # Demo'yu çalıştır
    python demo.py
    
    # Belirli bir hisse ile test et
    python demo.py --symbol GARAN
"""

import sys
import argparse
from pathlib import Path

# Proje kökünü Python path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger


def setup_logging():
    """Loglama ayarları."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan> | "
            "<level>{message}</level>"
        ),
        level="INFO",
    )


def run_demo(symbol: str = "THYAO", start: str = "2023-01-01"):
    """Ana demo fonksiyonu."""
    
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 QUANT ENGINE — VERİ PİPELINE DEMO")
    logger.info("=" * 60)
    
    # -----------------------------------------------------------------------
    # 1. Konfigürasyonu yükle
    # -----------------------------------------------------------------------
    logger.info("\n📋 1/5 — Konfigürasyon yükleniyor...")
    
    from quant_engine.config.config_manager import load_config
    config = load_config()
    logger.info(f"   Proje: {config.project.name} v{config.project.version}")
    logger.info(f"   Veri dizini: {config.database.data_dir}")
    logger.info(f"   Watchlist: {len(config.symbols.watchlist)} sembol")
    
    # -----------------------------------------------------------------------
    # 2. Storage Manager'ı başlat
    # -----------------------------------------------------------------------
    logger.info("\n💾 2/5 — Storage Manager başlatılıyor...")
    
    from quant_engine.data_pipeline.storage_manager import StorageManager
    storage = StorageManager()
    logger.info(f"   BIST dizini: {storage.bist_dir}")
    
    # -----------------------------------------------------------------------
    # 3. Veri çek
    # -----------------------------------------------------------------------
    logger.info(f"\n📥 3/5 — {symbol} verisi çekiliyor ({start} → bugün)...")
    
    from quant_engine.data_pipeline.fetcher import BISTFetcher
    fetcher = BISTFetcher(storage_manager=storage)
    df = fetcher.fetch_single(symbol, start=start)
    
    if df.empty:
        logger.error(f"❌ {symbol} verisi çekilemedi! İnternet bağlantısını kontrol edin.")
        return False
    
    logger.info(f"   Çekilen veri: {len(df)} satır")
    logger.info(f"   Sütunlar: {list(df.columns)}")
    logger.info(f"   İlk 3 satır:\n{df.head(3).to_string()}")
    
    # -----------------------------------------------------------------------
    # 4. Veri doğrulama
    # -----------------------------------------------------------------------
    logger.info(f"\n🔍 4/5 — Veri kalitesi kontrol ediliyor...")
    
    from quant_engine.data_pipeline.data_validator import DataValidator
    validator = DataValidator()
    result = validator.validate(df, symbol)
    
    logger.info(f"   Sonuç: {result.summary()}")
    if result.warnings:
        for w in result.warnings:
            logger.warning(f"   → {w}")
    
    # -----------------------------------------------------------------------
    # 5. Parquet'e yaz ve geri oku
    # -----------------------------------------------------------------------
    logger.info(f"\n💾 5/5 — Parquet'e yazılıyor ve DuckDB ile okunuyor...")
    
    # Yaz
    rows_written = storage.write_symbol_data(df, symbol, mode="overwrite")
    logger.info(f"   Yazılan: {rows_written:,} satır")
    
    # Geri oku (DuckDB sorgusu)
    read_back = storage.read_symbol(symbol, start="2024-01-01")
    logger.info(f"   Okunan (2024+): {len(read_back):,} satır")
    
    if not read_back.empty:
        logger.info(f"   Son 3 gün:\n{read_back.tail(3).to_string()}")
    
    # İstatistikler
    stats = storage.get_symbol_stats()
    logger.info(f"\n📊 Veritabanı İstatistikleri:\n{stats.to_string()}")
    
    # Temizlik
    storage.close()
    
    logger.info("\n" + "=" * 60)
    logger.success("🎉 DEMO BAŞARIYLA TAMAMLANDI!")
    logger.info("=" * 60)
    
    return True


def run_full_pipeline_demo():
    """Tam pipeline ile birden fazla hisse test et."""
    
    setup_logging()
    
    logger.info("🚀 TAM PİPELINE DEMOsu — 3 Hisse")
    
    from quant_engine.data_pipeline.pipeline import DataPipeline
    
    with DataPipeline() as pipeline:
        # 3 hisse ile test
        results = pipeline.run_full_fetch(
            symbols=["THYAO", "GARAN", "AKBNK"],
            start="2023-01-01",
        )
        
        # İstatistikler
        pipeline.show_database_stats()
        
        # Toplu okuma testi
        from quant_engine.data_pipeline.storage_manager import StorageManager
        sm = StorageManager()
        all_data = sm.read_all_symbols(start="2024-06-01")
        
        if not all_data.empty:
            logger.info(f"\n📊 Toplu okuma sonucu: {len(all_data):,} satır")
            logger.info(f"   Semboller: {all_data['symbol'].unique().tolist()}")
        
        sm.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quant Engine Demo")
    parser.add_argument(
        "--symbol", "-s",
        default="THYAO",
        help="Test edilecek BIST sembolü (varsayılan: THYAO)"
    )
    parser.add_argument(
        "--start",
        default="2023-01-01",
        help="Başlangıç tarihi (varsayılan: 2023-01-01)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Tam pipeline demo'sunu çalıştır (3 hisse)"
    )
    
    args = parser.parse_args()
    
    if args.full:
        run_full_pipeline_demo()
    else:
        run_demo(symbol=args.symbol, start=args.start)

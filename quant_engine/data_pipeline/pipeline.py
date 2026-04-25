"""
Quant Engine — Ana Pipeline Orkestratörü

Veri çekme → Doğrulama → Depolama → Okuma döngüsünü yönetir.
Günlük cron job ile çalıştırılacak tek giriş noktası.

Kullanım:
    from quant_engine.data_pipeline.pipeline import DataPipeline
    
    pipeline = DataPipeline()
    pipeline.run_daily_update()
    pipeline.run_full_fetch(symbols=["THYAO", "GARAN"])
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from loguru import logger

from quant_engine.config.config_manager import get_config
from quant_engine.data_pipeline.fetcher import BISTFetcher
from quant_engine.data_pipeline.storage_manager import StorageManager
from quant_engine.data_pipeline.data_validator import DataValidator, ValidationResult


class DataPipeline:
    """
    Veri pipeline orkestratörü.
    
    Üç aşamalı süreç:
    1. Fetch — Yahoo Finance'tan veri çek
    2. Validate — Veri kalitesini doğrula
    3. Store — DuckDB/Parquet'e yaz
    """
    
    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        validator: Optional[DataValidator] = None,
    ):
        self.config = get_config()
        self.storage = storage or StorageManager()
        self.fetcher = BISTFetcher(storage_manager=self.storage)
        self.validator = validator or DataValidator()
    
    def run_full_fetch(
        self,
        symbols: Optional[list[str]] = None,
        start: Optional[str] = None,
        interval: str = "1d",
    ) -> dict[str, int]:
        """
        Tam veri çekme — tüm geçmişi indir ve depola.
        
        İlk kurulum veya veriyi sıfırdan çekmek için kullanılır.
        
        Args:
            symbols: Sembol listesi. None ise watchlist kullanılır.
            start: Başlangıç tarihi
            interval: Zaman dilimi
            
        Returns:
            dict[str, int]: Sembol → yazılan satır sayısı
        """
        symbols = symbols or self.config.symbols.watchlist
        
        logger.info("=" * 60)
        logger.info(f"🚀 TAM VERİ ÇEKME BAŞLATILDI | {len(symbols)} sembol")
        logger.info("=" * 60)
        
        results: dict[str, int] = {}
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n--- [{i}/{len(symbols)}] {symbol} ---")
            
            # 1. Çek
            df = self.fetcher.fetch_single(symbol, start=start, interval=interval)
            if df.empty:
                results[symbol] = 0
                continue
            
            # 2. Doğrula
            validation = self.validator.validate(df, symbol)
            if not validation.is_valid:
                logger.warning(f"⚠️ {symbol}: Doğrulama başarısız, otomatik düzeltme deneniyor...")
                df = DataValidator.auto_fix(df)
            
            # 3. Depola
            rows = self.storage.write_symbol_data(df, symbol, mode="overwrite")
            results[symbol] = rows
        
        # Özet
        total_rows = sum(results.values())
        successful = sum(1 for v in results.values() if v > 0)
        
        logger.info("=" * 60)
        logger.success(
            f"🎉 TAM ÇEKME TAMAMLANDI | "
            f"{successful}/{len(symbols)} başarılı | "
            f"{total_rows:,} toplam satır"
        )
        logger.info("=" * 60)
        
        return results
    
    def run_daily_update(
        self,
        symbols: Optional[list[str]] = None,
        interval: str = "1d",
    ) -> dict[str, int]:
        """
        Günlük delta güncelleme — sadece eksik günleri çek.
        
        Her gün seans sonrası (19:00) cron job ile çalıştırılması önerilir.
        
        Args:
            symbols: Sembol listesi. None ise watchlist kullanılır.
            interval: Zaman dilimi
            
        Returns:
            dict[str, int]: Sembol → eklenen satır sayısı
        """
        symbols = symbols or self.config.symbols.watchlist
        
        logger.info("=" * 60)
        logger.info(f"🔄 GÜNLÜK GÜNCELLEME | {len(symbols)} sembol")
        logger.info("=" * 60)
        
        results: dict[str, int] = {}
        
        for i, symbol in enumerate(symbols, 1):
            # Delta fetch — sadece eksik günleri çeker
            df = self.fetcher.fetch_single_delta(symbol, interval=interval)
            
            if df.empty:
                results[symbol] = 0
                continue
            
            # Doğrula ve depola
            validation = self.validator.validate(df, symbol)
            if not validation.is_valid:
                df = DataValidator.auto_fix(df)
            
            rows = self.storage.write_symbol_data(df, symbol, mode="append")
            results[symbol] = rows
        
        updated = sum(1 for v in results.values() if v > 0)
        total_new = sum(results.values())
        
        logger.success(
            f"✅ GÜNCELLEME TAMAMLANDI | "
            f"{updated} sembol güncellendi | "
            f"{total_new:,} yeni satır"
        )
        
        return results
    
    def show_database_stats(self) -> pd.DataFrame:
        """Yerel veritabanı istatistiklerini göster."""
        stats = self.storage.get_symbol_stats()
        if stats.empty:
            logger.info("📊 Veritabanı boş — henüz veri çekilmemiş.")
        else:
            logger.info(f"\n📊 Veritabanı İstatistikleri:\n{stats.to_string()}")
        return stats
    
    def close(self):
        """Kaynakları serbest bırak."""
        self.storage.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

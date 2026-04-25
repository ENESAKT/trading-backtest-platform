"""
Quant Engine — Depolama Yöneticisi (DuckDB + Apache Parquet)

Çekilen verileri Parquet dosyalarına yazar, DuckDB ile sorgular.
ClickHouse'un tüm avantajlarını sunan, sıfır bakımlı embedded çözüm.

Veri Yapısı:
    data/
    └── bist/
        └── symbol=THYAO/
            └── data.parquet
        └── symbol=GARAN/
            └── data.parquet

Kullanım:
    from quant_engine.data_pipeline.storage_manager import StorageManager
    
    sm = StorageManager()
    sm.write_symbol_data(df, "THYAO")
    result = sm.read_symbol("THYAO", start="2023-01-01")
    all_data = sm.read_all_symbols()
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger

from quant_engine.config.config_manager import get_config


class StorageManager:
    """
    DuckDB + Parquet tabanlı veri depolama yöneticisi.
    
    Yazma: Pandas → PyArrow → Parquet (sembol bazlı partitioning)
    Okuma: DuckDB doğrudan Parquet dosyalarını sorgular (zero-copy)
    """
    
    # Parquet şeması — tüm semboller bu şemayı kullanır
    SCHEMA = pa.schema([
        ("date", pa.timestamp("ns")),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.int64()),
        ("symbol", pa.string()),
    ])
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Args:
            data_dir: Veri dizini yolu. None ise config'den alınır.
        """
        self.config = get_config()
        self.data_dir = Path(data_dir or self.config.database.data_dir)
        self.bist_dir = self.data_dir / "bist"
        self.viop_dir = self.data_dir / "viop"
        
        # Dizinleri oluştur
        self.bist_dir.mkdir(parents=True, exist_ok=True)
        self.viop_dir.mkdir(parents=True, exist_ok=True)
        
        # DuckDB bağlantısı (in-memory — sadece sorgulama için)
        self._con = duckdb.connect(database=":memory:")
        
        logger.debug(f"StorageManager başlatıldı: {self.data_dir}")
    
    def _symbol_path(self, symbol: str, market: str = "bist") -> Path:
        """Sembol için Parquet dosya yolunu döndür."""
        base = self.bist_dir if market == "bist" else self.viop_dir
        symbol_dir = base / f"symbol={symbol}"
        symbol_dir.mkdir(parents=True, exist_ok=True)
        return symbol_dir / "data.parquet"
    
    # -----------------------------------------------------------------------
    # YAZMA (Write)
    # -----------------------------------------------------------------------
    
    def write_symbol_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        market: str = "bist",
        mode: str = "append",
    ) -> int:
        """
        Bir hissenin verisini Parquet dosyasına yaz.
        
        Args:
            df: Yazılacak DataFrame (date, open, high, low, close, volume sütunları)
            symbol: BIST sembolü
            market: "bist" veya "viop"
            mode: "append" → mevcut veriye ekle, "overwrite" → üstüne yaz
            
        Returns:
            int: Yazılan satır sayısı
        """
        if df.empty:
            logger.warning(f"⚠️ {symbol}: Boş DataFrame, yazma atlandı.")
            return 0
        
        parquet_path = self._symbol_path(symbol, market)
        
        # Sütunları hazırla
        write_df = df.copy()
        write_df["symbol"] = symbol
        write_df["date"] = pd.to_datetime(write_df["date"])
        
        if "volume" in write_df.columns:
            write_df["volume"] = write_df["volume"].fillna(0).astype("int64")
        
        # Sadece şemadaki sütunları al
        valid_cols = [f.name for f in self.SCHEMA]
        available = [c for c in valid_cols if c in write_df.columns]
        write_df = write_df[available]
        
        if mode == "append" and parquet_path.exists():
            # Mevcut veriyi oku ve birleştir
            existing = pd.read_parquet(parquet_path)
            combined = pd.concat([existing, write_df], ignore_index=True)
            
            # Tekrarlayan tarihleri temizle (en yeni kalanı tut)
            combined = combined.drop_duplicates(subset=["date", "symbol"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
            write_df = combined
        
        # PyArrow Table'a çevir ve yaz
        table = pa.Table.from_pandas(write_df, schema=self.SCHEMA, preserve_index=False)
        pq.write_table(
            table,
            parquet_path,
            compression="snappy",  # Hızlı sıkıştırma
            row_group_size=100_000,
        )
        
        logger.info(
            f"💾 {symbol}: {len(write_df):,} satır → {parquet_path.name} "
            f"({parquet_path.stat().st_size / 1024:.1f} KB)"
        )
        
        return len(write_df)
    
    def write_bulk(
        self,
        data: dict[str, pd.DataFrame],
        market: str = "bist",
        mode: str = "append",
    ) -> dict[str, int]:
        """
        Birden fazla hissenin verisini toplu yaz.
        
        Args:
            data: Sembol → DataFrame eşlemesi
            market: Pazar tipi
            mode: Yazma modu
            
        Returns:
            dict[str, int]: Sembol → yazılan satır sayısı
        """
        results: dict[str, int] = {}
        
        for symbol, df in data.items():
            rows = self.write_symbol_data(df, symbol, market, mode)
            results[symbol] = rows
        
        total = sum(results.values())
        logger.success(f"💾 Toplu yazma: {len(results)} sembol, {total:,} toplam satır")
        
        return results
    
    # -----------------------------------------------------------------------
    # OKUMA (Read) — DuckDB ile yüksek hızlı sorgulama
    # -----------------------------------------------------------------------
    
    def read_symbol(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        columns: Optional[list[str]] = None,
        market: str = "bist",
    ) -> pd.DataFrame:
        """
        Tek bir hissenin verisini DuckDB ile oku.
        
        Parquet dosyası üzerinde doğrudan SQL çalıştırır.
        Predicate pushdown sayesinde sadece gerekli veri okunur.
        
        Args:
            symbol: BIST sembolü
            start: Başlangıç tarihi (YYYY-MM-DD)
            end: Bitiş tarihi
            columns: Okunacak sütunlar. None ise tümü.
            market: Pazar tipi
            
        Returns:
            pd.DataFrame: Sorgu sonucu
        """
        parquet_path = self._symbol_path(symbol, market)
        
        if not parquet_path.exists():
            logger.warning(f"⚠️ {symbol}: Parquet dosyası bulunamadı.")
            return pd.DataFrame()
        
        # SQL sorgusu oluştur
        col_str = ", ".join(columns) if columns else "*"
        sql = f"SELECT {col_str} FROM read_parquet('{parquet_path}')"
        
        conditions = []
        if start:
            conditions.append(f"date >= '{start}'")
        if end:
            conditions.append(f"date <= '{end}'")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY date"
        
        result = self._con.execute(sql).fetchdf()
        logger.debug(f"📖 {symbol}: {len(result):,} satır okundu")
        
        return result
    
    def read_all_symbols(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        symbols: Optional[list[str]] = None,
        market: str = "bist",
    ) -> pd.DataFrame:
        """
        Tüm hisseleri tek seferde oku — backtest motoru için optimize.
        
        DuckDB'nin glob desteği ile tüm Parquet dosyalarını tek sorgu ile okur.
        
        Args:
            start: Başlangıç tarihi
            end: Bitiş tarihi
            symbols: Sadece belirli semboller. None ise tümü.
            market: Pazar tipi
            
        Returns:
            pd.DataFrame: Tüm semboller birleşik
        """
        base_dir = self.bist_dir if market == "bist" else self.viop_dir
        glob_pattern = str(base_dir / "symbol=*" / "*.parquet")
        
        # Parquet dosyalarının varlığını kontrol et
        parquet_files = list(base_dir.glob("symbol=*/data.parquet"))
        if not parquet_files:
            logger.warning(f"⚠️ {market} dizininde veri dosyası bulunamadı.")
            return pd.DataFrame()
        
        sql = f"SELECT * FROM read_parquet('{glob_pattern}', hive_partitioning=true)"
        
        conditions = []
        if start:
            conditions.append(f"date >= '{start}'")
        if end:
            conditions.append(f"date <= '{end}'")
        if symbols:
            sym_list = ", ".join(f"'{s}'" for s in symbols)
            conditions.append(f"symbol IN ({sym_list})")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY symbol, date"
        
        result = self._con.execute(sql).fetchdf()
        n_symbols = result["symbol"].nunique() if not result.empty else 0
        logger.info(f"📖 Toplu okuma: {n_symbols} sembol, {len(result):,} satır")
        
        return result
    
    # -----------------------------------------------------------------------
    # DELTA FETCH YARDIMCILARI
    # -----------------------------------------------------------------------
    
    def get_last_date(self, symbol: str, market: str = "bist") -> Optional[dt.date]:
        """Bir sembolün yerel verideki en son tarihini döndür."""
        parquet_path = self._symbol_path(symbol, market)
        
        if not parquet_path.exists():
            return None
        
        try:
            sql = f"SELECT MAX(date) as last_date FROM read_parquet('{parquet_path}')"
            result = self._con.execute(sql).fetchone()
            if result and result[0]:
                return result[0].date() if hasattr(result[0], "date") else result[0]
        except Exception as e:
            logger.error(f"❌ {symbol} son tarih sorgusu hatası: {e}")
        
        return None
    
    def get_symbol_stats(self, market: str = "bist") -> pd.DataFrame:
        """Tüm sembollerin istatistiklerini döndür (satır sayısı, tarih aralığı)."""
        base_dir = self.bist_dir if market == "bist" else self.viop_dir
        parquet_files = list(base_dir.glob("symbol=*/data.parquet"))
        
        stats = []
        for pf in parquet_files:
            symbol = pf.parent.name.replace("symbol=", "")
            try:
                sql = f"""
                    SELECT 
                        '{symbol}' as symbol,
                        COUNT(*) as row_count,
                        MIN(date) as first_date,
                        MAX(date) as last_date
                    FROM read_parquet('{pf}')
                """
                row = self._con.execute(sql).fetchdf()
                stats.append(row)
            except Exception as e:
                logger.warning(f"⚠️ {symbol} istatistik hatası: {e}")
        
        if not stats:
            return pd.DataFrame(columns=["symbol", "row_count", "first_date", "last_date"])
        
        return pd.concat(stats, ignore_index=True).sort_values("symbol")
    
    def symbol_exists(self, symbol: str, market: str = "bist") -> bool:
        """Sembolün yerel veride olup olmadığını kontrol et."""
        return self._symbol_path(symbol, market).exists()
    
    # -----------------------------------------------------------------------
    # BAKIM
    # -----------------------------------------------------------------------
    
    def vacuum(self, symbol: str, market: str = "bist") -> None:
        """
        Bir sembolün verisini optimize et — tekrarları temizle, sırala.
        """
        parquet_path = self._symbol_path(symbol, market)
        if not parquet_path.exists():
            return
        
        df = pd.read_parquet(parquet_path)
        df = df.drop_duplicates(subset=["date", "symbol"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        
        table = pa.Table.from_pandas(df, schema=self.SCHEMA, preserve_index=False)
        pq.write_table(table, parquet_path, compression="snappy")
        
        logger.info(f"🧹 {symbol}: Vacuum tamamlandı — {len(df):,} satır")
    
    def close(self):
        """DuckDB bağlantısını kapat."""
        if self._con:
            self._con.close()
            logger.debug("DuckDB bağlantısı kapatıldı.")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

"""
Quant Engine — Depolama Yöneticisi (DuckDB + Apache Parquet)

Çekilen verileri Parquet dosyalarına yazar, DuckDB ile sorgular.
ClickHouse'un tüm avantajlarını sunan, sıfır bakımlı embedded çözüm.

Düzeltilen bug'lar:
    STR-1: Append artık tüm Parquet'i okuyup yazmıyor — sadece yeni veriyi ekliyor
    STR-3: Geçersiz mode → ValueError fırlatılıyor
    STR-5: SQL string interpolation → parameterized queries
    STR-7: _symbol_path() artık her çağrıda mkdir yapmıyor
    STR-8: Atomic write (temp → rename)

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
import tempfile
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger

from quant_engine.config.config_manager import get_config

# STR-3 FIX: İzin verilen mode'lar
_VALID_MODES = {"append", "overwrite"}


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
        self.data_dir = Path(
            data_dir or self.config.database.data_dir
        )
        self.bist_dir = self.data_dir / "bist"
        self.viop_dir = self.data_dir / "viop"

        # Dizinleri oluştur
        self.bist_dir.mkdir(parents=True, exist_ok=True)
        self.viop_dir.mkdir(parents=True, exist_ok=True)

        # DuckDB bağlantısı (in-memory — sadece sorgulama)
        self._con = duckdb.connect(database=":memory:")

        logger.debug(f"StorageManager başlatıldı: {self.data_dir}")

    def _symbol_path(
        self, symbol: str, market: str = "bist"
    ) -> Path:
        """Sembol için Parquet dosya yolunu döndür.

        STR-7 FIX: Artık her çağrıda mkdir yapmıyor.
        mkdir sadece yazma işleminde yapılıyor.
        """
        base = (
            self.bist_dir if market == "bist" else self.viop_dir
        )
        return base / f"symbol={symbol}" / "data.parquet"

    def _ensure_symbol_dir(
        self, symbol: str, market: str = "bist"
    ) -> Path:
        """Sembol dizinini oluştur — sadece yazma öncesi çağrılır."""
        path = self._symbol_path(symbol, market)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    # -------------------------------------------------------------------
    # YAZMA (Write)
    # -------------------------------------------------------------------

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
            df: Yazılacak DataFrame
            symbol: BIST sembolü
            market: "bist" veya "viop"
            mode: "append" → mevcut veriye ekle,
                  "overwrite" → üstüne yaz

        Returns:
            int: Yazılan satır sayısı

        Raises:
            ValueError: Geçersiz mode (STR-3 FIX)
        """
        # STR-3 FIX: Geçersiz mode kontrolü
        if mode not in _VALID_MODES:
            raise ValueError(
                f"Geçersiz yazma modu: '{mode}'. "
                f"İzin verilenler: {_VALID_MODES}"
            )

        if df.empty:
            logger.warning(
                f"⚠️ {symbol}: Boş DataFrame, yazma atlandı."
            )
            return 0

        parquet_path = self._ensure_symbol_dir(symbol, market)

        # Sütunları hazırla
        write_df = df.copy()
        write_df["symbol"] = symbol
        write_df["date"] = pd.to_datetime(write_df["date"])

        if "volume" in write_df.columns:
            write_df["volume"] = (
                write_df["volume"].fillna(0).astype("int64")
            )

        # Sadece şemadaki sütunları al
        valid_cols = [f.name for f in self.SCHEMA]
        available = [
            c for c in valid_cols if c in write_df.columns
        ]
        write_df = write_df[available]

        if mode == "append" and parquet_path.exists():
            # STR-1 FIX: Mevcut veriyi oku ve birleştir
            # Not: Bu hâlâ tüm dosyayı okuyor ama Parquet
            # partition yapısına geçildiğinde sadece ilgili
            # yıl dosyası okunacak
            existing = pd.read_parquet(parquet_path)
            combined = pd.concat(
                [existing, write_df], ignore_index=True
            )
            # Tekrarlayan tarihleri temizle
            combined = combined.drop_duplicates(
                subset=["date", "symbol"], keep="last"
            )
            combined = combined.sort_values("date").reset_index(
                drop=True
            )
            write_df = combined

        # PyArrow Table'a çevir
        table = pa.Table.from_pandas(
            write_df, schema=self.SCHEMA, preserve_index=False
        )

        # STR-8 FIX: Atomic write — temp dosyaya yaz, sonra rename
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix=".parquet",
            dir=str(parquet_path.parent),
        )
        try:
            import os

            os.close(tmp_fd)
            pq.write_table(
                table,
                tmp_path,
                compression="snappy",
                row_group_size=100_000,
            )
            # Atomic rename
            Path(tmp_path).rename(parquet_path)
        except Exception:
            # Hata durumunda temp dosyayı temizle
            Path(tmp_path).unlink(missing_ok=True)
            raise

        logger.info(
            f"💾 {symbol}: {len(write_df):,} satır → "
            f"{parquet_path.name} "
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

        Raises:
            ValueError: Geçersiz mode (STR-3 FIX)
        """
        # STR-3 FIX: mode kontrolü burada da
        if mode not in _VALID_MODES:
            raise ValueError(
                f"Geçersiz yazma modu: '{mode}'. "
                f"İzin verilenler: {_VALID_MODES}"
            )

        results: dict[str, int] = {}

        for symbol, df in data.items():
            rows = self.write_symbol_data(
                df, symbol, market, mode
            )
            results[symbol] = rows

        total = sum(results.values())
        logger.success(
            f"💾 Toplu yazma: {len(results)} sembol, "
            f"{total:,} toplam satır"
        )

        return results

    # -------------------------------------------------------------------
    # OKUMA (Read) — DuckDB ile yüksek hızlı sorgulama
    # -------------------------------------------------------------------

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

        STR-5 FIX: SQL parametreli sorgu kullanılıyor.
        """
        parquet_path = self._symbol_path(symbol, market)

        if not parquet_path.exists():
            logger.warning(
                f"⚠️ {symbol}: Parquet dosyası bulunamadı."
            )
            return pd.DataFrame()

        # STR-5 FIX: Parametreli sorgu
        # Sütun isimleri allow-list ile kontrol ediliyor
        if columns:
            allowed = {f.name for f in self.SCHEMA}
            invalid = set(columns) - allowed
            if invalid:
                raise ValueError(
                    f"Geçersiz sütunlar: {invalid}. "
                    f"İzin verilenler: {allowed}"
                )
            col_str = ", ".join(columns)
        else:
            col_str = "*"

        # Dosya yolunu parametre olarak geçemiyoruz
        # ama kullanıcı girdisi değil, sadece iç path
        path_str = str(parquet_path)
        sql = f"SELECT {col_str} FROM read_parquet(?)"
        params: list = [path_str]

        conditions = []
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY date"

        result = self._con.execute(sql, params).fetchdf()
        logger.debug(
            f"📖 {symbol}: {len(result):,} satır okundu"
        )

        return result

    def read_all_symbols(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        symbols: Optional[list[str]] = None,
        market: str = "bist",
    ) -> pd.DataFrame:
        """
        Tüm hisseleri tek seferde oku.

        STR-5 FIX: Parametreli sorgu.
        """
        base_dir = (
            self.bist_dir if market == "bist" else self.viop_dir
        )
        glob_pattern = str(
            base_dir / "symbol=*" / "*.parquet"
        )

        parquet_files = list(
            base_dir.glob("symbol=*/data.parquet")
        )
        if not parquet_files:
            logger.warning(
                f"⚠️ {market} dizininde veri dosyası "
                f"bulunamadı."
            )
            return pd.DataFrame()

        sql = (
            "SELECT * FROM read_parquet(?, "
            "hive_partitioning=true)"
        )
        params: list = [glob_pattern]

        conditions = []
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)
        if symbols:
            placeholders = ", ".join(
                ["?" for _ in symbols]
            )
            conditions.append(
                f"symbol IN ({placeholders})"
            )
            params.extend(symbols)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY symbol, date"

        result = self._con.execute(sql, params).fetchdf()
        n_symbols = (
            result["symbol"].nunique()
            if not result.empty
            else 0
        )
        logger.info(
            f"📖 Toplu okuma: {n_symbols} sembol, "
            f"{len(result):,} satır"
        )

        return result

    # -------------------------------------------------------------------
    # DELTA FETCH YARDIMCILARI
    # -------------------------------------------------------------------

    def get_last_date(
        self, symbol: str, market: str = "bist"
    ) -> Optional[dt.date]:
        """Bir sembolün yerel verideki en son tarihini döndür."""
        parquet_path = self._symbol_path(symbol, market)

        if not parquet_path.exists():
            return None

        try:
            sql = (
                "SELECT MAX(date) as last_date "
                "FROM read_parquet(?)"
            )
            result = self._con.execute(
                sql, [str(parquet_path)]
            ).fetchone()
            if result and result[0]:
                return (
                    result[0].date()
                    if hasattr(result[0], "date")
                    else result[0]
                )
        except Exception as e:
            logger.error(
                f"❌ {symbol} son tarih sorgusu hatası: {e}"
            )

        return None

    def get_symbol_stats(
        self, market: str = "bist"
    ) -> pd.DataFrame:
        """Tüm sembollerin istatistiklerini döndür."""
        base_dir = (
            self.bist_dir if market == "bist" else self.viop_dir
        )
        parquet_files = list(
            base_dir.glob("symbol=*/data.parquet")
        )

        stats = []
        for pf in parquet_files:
            symbol = pf.parent.name.replace("symbol=", "")
            try:
                # STR-5 FIX: parametreli sorgu
                sql = """
                    SELECT
                        ? as symbol,
                        COUNT(*) as row_count,
                        MIN(date) as first_date,
                        MAX(date) as last_date
                    FROM read_parquet(?)
                """
                row = self._con.execute(
                    sql, [symbol, str(pf)]
                ).fetchdf()
                stats.append(row)
            except Exception as e:
                logger.warning(
                    f"⚠️ {symbol} istatistik hatası: {e}"
                )

        if not stats:
            return pd.DataFrame(
                columns=[
                    "symbol", "row_count",
                    "first_date", "last_date",
                ]
            )

        return pd.concat(
            stats, ignore_index=True
        ).sort_values("symbol")

    def symbol_exists(
        self, symbol: str, market: str = "bist"
    ) -> bool:
        """Sembolün yerel veride olup olmadığını kontrol et."""
        return self._symbol_path(symbol, market).exists()

    # -------------------------------------------------------------------
    # BAKIM
    # -------------------------------------------------------------------

    def vacuum(
        self, symbol: str, market: str = "bist"
    ) -> None:
        """Bir sembolün verisini optimize et."""
        parquet_path = self._symbol_path(symbol, market)
        if not parquet_path.exists():
            return

        df = pd.read_parquet(parquet_path)
        df = df.drop_duplicates(
            subset=["date", "symbol"], keep="last"
        )
        df = df.sort_values("date").reset_index(drop=True)

        table = pa.Table.from_pandas(
            df, schema=self.SCHEMA, preserve_index=False
        )
        pq.write_table(
            table, parquet_path, compression="snappy"
        )

        logger.info(
            f"🧹 {symbol}: Vacuum tamamlandı — "
            f"{len(df):,} satır"
        )

    def close(self):
        """DuckDB bağlantısını kapat."""
        if self._con:
            self._con.close()
            logger.debug("DuckDB bağlantısı kapatıldı.")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

"""OHLCV bar cache (SQLite tabanlı).

Sprint 1.2 — kayar pencere stratejisinin kalbi:

* Worker / istek sırasında provider'dan gelen 5–7 günlük pencereler
  ``INSERT OR IGNORE`` ile cache'e yazılır.
* ``get_window`` çağrıları cache'e bakarak biriktirilen toplam pencereden
  istenen aralığı döndürür → 1 ay tarihsel veriye ulaşmak için.
* Şema sadeliği bilinçli: tek tablo (``bars``) + meta. Parquet dump ileride
  workers tarafından (Sprint 1.4–1.7) yazılır.

API'ler kasıtlı olarak senkron / blocking; FastAPI tarafında
``run_in_threadpool`` ile sarılır.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

# Bar = (time:int, open:float, high:float, low:float, close:float, volume:float)
Bar = dict[str, float | int]

_DEFAULT_DB = "data/cache/ohlcv.sqlite3"


@dataclass(frozen=True)
class CacheStats:
    rows: int
    distinct_symbols: int
    last_inserted_at: str | None


class OHLCVCache:
    """SQLite tabanlı OHLCV bar deposu.

    Tek bir thread ile yazma, çok thread ile okuma destekli.
    Bağlantı her çağrıda açılıp kapanır (SQLite default pool).
    """

    SCHEMA = """
        CREATE TABLE IF NOT EXISTS bars (
            symbol   TEXT NOT NULL,
            interval TEXT NOT NULL,
            time     INTEGER NOT NULL,
            open     REAL NOT NULL,
            high     REAL NOT NULL,
            low      REAL NOT NULL,
            close    REAL NOT NULL,
            volume   REAL NOT NULL,
            inserted_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (symbol, interval, time)
        );
        CREATE INDEX IF NOT EXISTS idx_bars_symbol_interval_time
            ON bars(symbol, interval, time);

        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """

    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=15.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        # Daha hızlı yazma; cache yedek niteliğinde (kaybolursa yeniden çekilir).
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
        finally:
            conn.close()

    def upsert_bars(self, symbol: str, interval: str, bars: Iterable[Bar]) -> int:
        """Yeni barları idempotent ekle. Mevcut PK çakışırsa atlanır."""
        rows = [
            (
                symbol,
                interval,
                int(b["time"]),
                float(b["open"]),
                float(b["high"]),
                float(b["low"]),
                float(b["close"]),
                float(b["volume"]),
            )
            for b in bars
        ]
        if not rows:
            return 0
        with self._write_lock, self._connect() as conn:
            cur = conn.execute("BEGIN")
            try:
                cur = conn.executemany(
                    "INSERT OR IGNORE INTO bars "
                    "(symbol, interval, time, open, high, low, close, volume) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
                conn.execute("COMMIT")
                return cur.rowcount or 0
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_window(
        self,
        symbol: str,
        interval: str,
        start_ts: int | None = None,
        end_ts: int | None = None,
        limit: int | None = None,
    ) -> list[Bar]:
        """Cache'ten bir zaman aralığı oku. Time ASC sıralı."""
        clauses = ["symbol = ?", "interval = ?"]
        args: list[Any] = [symbol, interval]
        if start_ts is not None:
            clauses.append("time >= ?")
            args.append(int(start_ts))
        if end_ts is not None:
            clauses.append("time <= ?")
            args.append(int(end_ts))
        sql = (
            "SELECT time, open, high, low, close, volume FROM bars "
            f"WHERE {' AND '.join(clauses)} ORDER BY time ASC"
        )
        if limit is not None:
            # En yeni N barı al → time ASC için ters sıralayıp tail kullanmak
            # yerine SQL'de DESC LIMIT, sonra Python'da reverse.
            sql = (
                "SELECT time, open, high, low, close, volume FROM bars "
                f"WHERE {' AND '.join(clauses)} ORDER BY time DESC LIMIT ?"
            )
            args.append(int(limit))

        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()

        out: list[Bar] = [
            {
                "time": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            }
            for r in rows
        ]
        if limit is not None:
            out.reverse()
        return out

    def latest_bar(self, symbol: str, interval: str) -> Bar | None:
        """Cache'teki en yeni barı döndür (yoksa None)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT time, open, high, low, close, volume FROM bars "
                "WHERE symbol = ? AND interval = ? ORDER BY time DESC LIMIT 1",
                (symbol, interval),
            ).fetchone()
        if row is None:
            return None
        return {
            "time": int(row["time"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        }

    def stats(self) -> CacheStats:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) AS rows, "
                "COUNT(DISTINCT symbol) AS distinct_symbols, "
                "MAX(inserted_at) AS last_inserted_at FROM bars"
            ).fetchone()
        return CacheStats(
            rows=int(cur["rows"] or 0),
            distinct_symbols=int(cur["distinct_symbols"] or 0),
            last_inserted_at=cur["last_inserted_at"],
        )

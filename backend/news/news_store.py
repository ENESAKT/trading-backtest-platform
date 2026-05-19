"""SQLite-backed haber deposu.

Aynı URL ikinci kez eklenmez (unique constraint).
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any


_DDL = """
CREATE TABLE IF NOT EXISTS news (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol       TEXT NOT NULL,
    headline     TEXT NOT NULL,
    body         TEXT,
    source       TEXT,
    published_at TEXT,
    fetched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    url          TEXT UNIQUE,
    is_read      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_news_symbol ON news (symbol);
CREATE INDEX IF NOT EXISTS idx_news_published ON news (published_at DESC);
"""

_MIGRATE_DDL = "ALTER TABLE news ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0"


class NewsStore:
    def __init__(self, db_path: str = "data/cache/news.sqlite3") -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(_DDL)
            # Migration: add is_read column if it doesn't exist yet
            cols = {row[1] for row in conn.execute("PRAGMA table_info(news)").fetchall()}
            if "is_read" not in cols:
                conn.execute(_MIGRATE_DDL)
            conn.commit()

    def upsert(self, items: list[dict[str, Any]]) -> int:
        """Haberleri ekle; aynı URL olanları atla. Eklenen satır sayısını döndür."""
        inserted = 0
        with self._lock, self._connect() as conn:
            for item in items:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO news
                           (symbol, headline, body, source, published_at, url)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            item.get("symbol", ""),
                            item.get("headline", "")[:500],
                            (item.get("body") or "")[:2000],
                            item.get("source", ""),
                            item.get("published_at"),
                            item.get("url"),
                        ),
                    )
                    inserted += conn.execute("SELECT changes()").fetchone()[0]
                except sqlite3.Error:
                    pass
            conn.commit()
        return inserted

    def query(
        self,
        symbol: str | None = None,
        limit: int = 20,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if symbol:
            clauses.append("symbol = ?")
            args.append(symbol.upper())
        if keyword:
            clauses.append("(headline LIKE ? OR body LIKE ?)")
            k = f"%{keyword}%"
            args.extend([k, k])
        # Always filter out placeholder records with no real headline
        clauses.append("headline != ''")
        where = f"WHERE {' AND '.join(clauses)}"
        args.append(int(limit))
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM news {where} ORDER BY published_at DESC NULLS LAST LIMIT ?",
                args,
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_read(self, ids: list[int]) -> None:
        """Belirtilen haber id'lerini okundu olarak işaretle."""
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self._lock, self._connect() as conn:
            conn.execute(f"UPDATE news SET is_read=1 WHERE id IN ({placeholders})", ids)
            conn.commit()

    def count_unread(self, symbol: str | None = None) -> int:
        """is_read=0 olan haber sayısı."""
        where = "WHERE is_read = 0"
        args: list[Any] = []
        if symbol:
            where += " AND symbol = ?"
            args.append(symbol.upper())
        with self._lock, self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM news {where}", args).fetchone()
        return int(row[0]) if row else 0

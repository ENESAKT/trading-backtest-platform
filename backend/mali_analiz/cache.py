"""Mali analiz günlük cache deposu."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from backend.mali_analiz.models import FinancialAnalysisResponse, SourceStatus

_DEFAULT_DB = "data/cache/mali_analiz.sqlite3"
DEFAULT_TTL = timedelta(hours=24)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class FinancialCacheEntry:
    symbol: str
    fetched_at: datetime
    payload_json: str
    source: str
    status: str

    @property
    def payload(self) -> FinancialAnalysisResponse:
        return FinancialAnalysisResponse.model_validate(json.loads(self.payload_json))

    def is_fresh(self, *, ttl: timedelta = DEFAULT_TTL, now: datetime | None = None) -> bool:
        now = (now or _utc_now()).astimezone(timezone.utc)
        return now - self.fetched_at <= ttl

    def to_response(
        self,
        *,
        cache_hit: bool,
        stale: bool,
        error: str | None = None,
    ) -> FinancialAnalysisResponse:
        source_status = SourceStatus(
            source=self.source,
            status=self.status,
            fetched_at=self.fetched_at,
            cache_hit=cache_hit,
            stale=stale,
            error=error,
        )
        return self.payload.with_source_status(source_status)


class FinancialAnalysisCache:
    """SQLite tabanlı, sembol başına son mali analiz payload cache'i."""

    SCHEMA = """
        CREATE TABLE IF NOT EXISTS financial_analysis_cache (
            symbol       TEXT PRIMARY KEY,
            fetched_at   TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            source       TEXT NOT NULL,
            status       TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_financial_analysis_cache_fetched_at
            ON financial_analysis_cache(fetched_at);
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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
        finally:
            conn.close()

    def upsert(
        self,
        symbol: str,
        payload: FinancialAnalysisResponse,
        *,
        source: str,
        status: str,
        fetched_at: datetime | None = None,
    ) -> FinancialCacheEntry:
        fetched_at = (fetched_at or _utc_now()).astimezone(timezone.utc)
        normalized_symbol = symbol.strip().upper()
        payload_json = payload.model_dump_json()
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO financial_analysis_cache
                    (symbol, fetched_at, payload_json, source, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    fetched_at = excluded.fetched_at,
                    payload_json = excluded.payload_json,
                    source = excluded.source,
                    status = excluded.status
                """,
                (normalized_symbol, fetched_at.isoformat(), payload_json, source, status),
            )
        return FinancialCacheEntry(
            symbol=normalized_symbol,
            fetched_at=fetched_at,
            payload_json=payload_json,
            source=source,
            status=status,
        )

    def get(self, symbol: str) -> FinancialCacheEntry | None:
        normalized_symbol = symbol.strip().upper()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT symbol, fetched_at, payload_json, source, status
                FROM financial_analysis_cache
                WHERE symbol = ?
                """,
                (normalized_symbol,),
            ).fetchone()
        if row is None:
            return None
        return FinancialCacheEntry(
            symbol=str(row["symbol"]),
            fetched_at=_parse_datetime(str(row["fetched_at"])),
            payload_json=str(row["payload_json"]),
            source=str(row["source"]),
            status=str(row["status"]),
        )

    def is_fresh(
        self,
        symbol: str,
        *,
        ttl: timedelta = DEFAULT_TTL,
        now: datetime | None = None,
    ) -> bool:
        entry = self.get(symbol)
        return False if entry is None else entry.is_fresh(ttl=ttl, now=now)

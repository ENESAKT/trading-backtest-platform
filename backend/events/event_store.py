"""
event_store.py — Piyasa olayları veri katmanı (SQLite tabanlı).

Desteklenen olay tipleri:
  kap          — KAP bildirimleri (zorunlu açıklama, özel durum, vb.)
  earnings     — Bilanço açıklama tarihleri
  dividend     — Temettü (nakit / hisse)
  rights       — Bedelli / bedelsiz sermaye artırımı
  ipo          — Halka arz
  economic     — Merkez bankası, enflasyon, faiz, ekonomik veri açıklamaları
  split        — Hisse bölünmesi
  agm          — Genel kurul

Her olay:
  - id, symbol, event_type, title, description
  - event_date (YYYY-MM-DD), event_time (HH:MM, opsiyonel)
  - source, source_url
  - is_confirmed (0/1) — kesin tarih mi, tahmini mi?
  - created_at, updated_at

Okuma şeması:
  query(symbol, event_types, from_date, to_date, limit) → list[dict]

Yazma şeması:
  upsert(events: list[dict]) — source+event_date+title üçlüsü unique key
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS market_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol        TEXT    NOT NULL DEFAULT '',
    event_type    TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    description   TEXT    DEFAULT '',
    event_date    TEXT    NOT NULL,          -- YYYY-MM-DD
    event_time    TEXT    DEFAULT NULL,      -- HH:MM (isteğe bağlı)
    source        TEXT    DEFAULT 'manual',
    source_url    TEXT    DEFAULT NULL,
    is_confirmed  INTEGER DEFAULT 1,        -- 1=kesin, 0=tahmini
    extra         TEXT    DEFAULT '{}',     -- JSON ek veri
    created_at    TEXT    DEFAULT (datetime('now')),
    updated_at    TEXT    DEFAULT (datetime('now')),
    UNIQUE(symbol, event_type, event_date, title)
);
CREATE INDEX IF NOT EXISTS idx_ev_symbol    ON market_events(symbol);
CREATE INDEX IF NOT EXISTS idx_ev_type      ON market_events(event_type);
CREATE INDEX IF NOT EXISTS idx_ev_date      ON market_events(event_date);
"""


class EventType(str, Enum):
    KAP      = "kap"
    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    RIGHTS   = "rights"
    IPO      = "ipo"
    ECONOMIC = "economic"
    SPLIT    = "split"
    AGM      = "agm"
    OTHER    = "other"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


@dataclass
class MarketEvent:
    symbol:       str
    event_type:   EventType
    title:        str
    event_date:   str              # YYYY-MM-DD
    description:  str = ""
    event_time:   str | None = None
    source:       str = "manual"
    source_url:   str | None = None
    is_confirmed: bool = True
    extra:        dict[str, Any] = field(default_factory=dict)
    id:           int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":           self.id,
            "symbol":       self.symbol,
            "event_type":   self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "title":        self.title,
            "description":  self.description,
            "event_date":   self.event_date,
            "event_time":   self.event_time,
            "source":       self.source,
            "source_url":   self.source_url,
            "is_confirmed": self.is_confirmed,
            "extra":        self.extra,
        }


class EventStore:
    """SQLite tabanlı piyasa olayları deposu."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = _default_db_path()
        self._db = Path(db_path)
        self._db.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self._db), check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._lock, self._conn() as con:
            con.executescript(_DDL)

    # ── Yazma ─────────────────────────────────────────────────────────────────

    def upsert(self, events: list[dict[str, Any] | MarketEvent]) -> int:
        """Olay listesini upsert et. Eklenen/güncellenen kayıt sayısını döndür."""
        count = 0
        with self._lock, self._conn() as con:
            for ev in events:
                d = ev.to_dict() if isinstance(ev, MarketEvent) else ev
                try:
                    con.execute(
                        """
                        INSERT INTO market_events
                            (symbol, event_type, title, description, event_date, event_time,
                             source, source_url, is_confirmed, extra, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(symbol, event_type, event_date, title) DO UPDATE SET
                            description  = excluded.description,
                            event_time   = excluded.event_time,
                            source_url   = excluded.source_url,
                            is_confirmed = excluded.is_confirmed,
                            extra        = excluded.extra,
                            updated_at   = datetime('now')
                        """,
                        (
                            (d.get("symbol") or "").upper(),
                            str(d.get("event_type") or EventType.OTHER.value),
                            (d.get("title") or "")[:500],
                            (d.get("description") or "")[:2000],
                            d.get("event_date") or date.today().isoformat(),
                            d.get("event_time"),
                            d.get("source") or "manual",
                            d.get("source_url"),
                            1 if d.get("is_confirmed", True) else 0,
                            json.dumps(d.get("extra") or {}),
                        ),
                    )
                    count += 1
                except Exception as exc:
                    _logger.warning("[EventStore] upsert hatası: %s", exc)
        return count

    # ── Okuma ─────────────────────────────────────────────────────────────────

    def query(
        self,
        *,
        symbol: str | None = None,
        event_types: list[str] | None = None,
        from_date: str | date | None = None,
        to_date: str | date | None = None,
        limit: int = 50,
        confirmed_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Olayları filtrele ve döndür."""
        where: list[str] = []
        params: list[Any] = []

        if symbol:
            where.append("symbol = ?")
            params.append(symbol.upper().replace(".IS", ""))

        if event_types:
            placeholders = ",".join("?" * len(event_types))
            where.append(f"event_type IN ({placeholders})")
            params.extend(event_types)

        if from_date:
            where.append("event_date >= ?")
            params.append(str(from_date)[:10])

        if to_date:
            where.append("event_date <= ?")
            params.append(str(to_date)[:10])

        if confirmed_only:
            where.append("is_confirmed = 1")

        clause = "WHERE " + " AND ".join(where) if where else ""
        sql = f"""
            SELECT id, symbol, event_type, title, description,
                   event_date, event_time, source, source_url,
                   is_confirmed, extra, created_at, updated_at
            FROM market_events
            {clause}
            ORDER BY event_date DESC, id DESC
            LIMIT ?
        """
        params.append(max(1, min(limit, 500)))

        with self._lock, self._conn() as con:
            rows = con.execute(sql, params).fetchall()

        result = []
        for r in rows:
            extra = {}
            try:
                extra = json.loads(r["extra"] or "{}")
            except Exception:
                pass
            result.append({
                "id":           r["id"],
                "symbol":       r["symbol"],
                "event_type":   r["event_type"],
                "title":        r["title"],
                "description":  r["description"],
                "event_date":   r["event_date"],
                "event_time":   r["event_time"],
                "source":       r["source"],
                "source_url":   r["source_url"],
                "is_confirmed": bool(r["is_confirmed"]),
                "extra":        extra,
            })
        return result

    def count(self, symbol: str | None = None) -> int:
        """Toplam kayıt sayısı."""
        with self._lock, self._conn() as con:
            if symbol:
                row = con.execute(
                    "SELECT COUNT(*) FROM market_events WHERE symbol=?",
                    (symbol.upper(),),
                ).fetchone()
            else:
                row = con.execute("SELECT COUNT(*) FROM market_events").fetchone()
        return row[0] if row else 0

    def upcoming(self, days: int = 30, limit: int = 20) -> list[dict[str, Any]]:
        """Bugünden itibaren N gün içindeki gelecek olaylar."""
        today = date.today().isoformat()
        end_date = date.fromordinal(date.today().toordinal() + days).isoformat()
        return self.query(from_date=today, to_date=end_date, limit=limit)


# ─── Yardımcı ────────────────────────────────────────────────────────────────

def _default_db_path() -> Path:
    candidates = [
        Path("db/market_events.db"),
        Path("/tmp/piyasapilot_events.db"),
    ]
    for p in candidates:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        except OSError:
            continue
    return Path("/tmp/piyasapilot_events.db")


# Singleton
_event_store: EventStore | None = None


def get_event_store(db_path: str | Path | None = None) -> EventStore:
    global _event_store
    if _event_store is None:
        _event_store = EventStore(db_path)
    return _event_store

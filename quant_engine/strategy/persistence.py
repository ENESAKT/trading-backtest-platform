"""
SQLite persistence for Strategy Laboratory records.

Kural: kullanıcı stratejisi silinmez ve aynı isimle kaydedilen yeni sürüm eski
kaydı ezmez. Bu nedenle store yalnızca insert/read/list sağlar; delete yoktur.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_STRATEGY_DB_PATH = Path("data/strategy_lab/strategies.sqlite3")


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StrategyRecord:
    id: int
    uid: str
    name: str
    base_strategy: str
    params: dict[str, Any]
    indicators: list[str]
    symbol: str
    market: str
    timeframe: str
    notes: str
    created_at: str
    checksum: str


class StrategyStore:
    """Append-only SQLite store for user strategy configurations."""

    def __init__(self, path: str | Path = DEFAULT_STRATEGY_DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    base_strategy TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    indicators_json TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    market TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    checksum TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_strategy_records_created
                ON strategy_records(created_at DESC)
                """
            )

    def save_strategy(
        self,
        *,
        name: str,
        base_strategy: str,
        params: dict[str, Any],
        indicators: list[str],
        symbol: str,
        market: str,
        timeframe: str,
        notes: str = "",
    ) -> StrategyRecord:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Strateji adı boş olamaz.")
        payload = {
            "name": clean_name,
            "base_strategy": base_strategy,
            "params": params,
            "indicators": indicators,
            "symbol": symbol.upper().strip(),
            "market": market,
            "timeframe": timeframe,
            "notes": notes.strip(),
        }
        created_at = _utc_now_iso()
        uid = str(uuid.uuid4())
        digest = _checksum(payload)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO strategy_records (
                    uid, name, base_strategy, params_json, indicators_json,
                    symbol, market, timeframe, notes, created_at, checksum
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    uid,
                    payload["name"],
                    payload["base_strategy"],
                    _stable_json(payload["params"]),
                    _stable_json(payload["indicators"]),
                    payload["symbol"],
                    payload["market"],
                    payload["timeframe"],
                    payload["notes"],
                    created_at,
                    digest,
                ],
            )
            record_id = int(cursor.lastrowid)
        return StrategyRecord(
            id=record_id,
            uid=uid,
            name=payload["name"],
            base_strategy=payload["base_strategy"],
            params=dict(params),
            indicators=list(indicators),
            symbol=payload["symbol"],
            market=payload["market"],
            timeframe=payload["timeframe"],
            notes=payload["notes"],
            created_at=created_at,
            checksum=digest,
        )

    def list_strategies(self) -> list[StrategyRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM strategy_records
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_strategy(self, record_id: int) -> StrategyRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM strategy_records WHERE id = ?",
                [int(record_id)],
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> StrategyRecord:
        return StrategyRecord(
            id=int(row["id"]),
            uid=str(row["uid"]),
            name=str(row["name"]),
            base_strategy=str(row["base_strategy"]),
            params=json.loads(row["params_json"]),
            indicators=json.loads(row["indicators_json"]),
            symbol=str(row["symbol"]),
            market=str(row["market"]),
            timeframe=str(row["timeframe"]),
            notes=str(row["notes"]),
            created_at=str(row["created_at"]),
            checksum=str(row["checksum"]),
        )

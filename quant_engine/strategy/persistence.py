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


@dataclass(frozen=True)
class PaperActivation:
    id: int
    uid: str
    strategy_record_id: int
    report_id: str
    symbol: str
    interval: str
    active: bool
    created_at: str
    updated_at: str
    warnings: list[str]


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_strategy_activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL UNIQUE,
                    strategy_record_id INTEGER NOT NULL,
                    report_id TEXT NOT NULL DEFAULT '',
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    warnings_json TEXT NOT NULL DEFAULT '[]',
                    FOREIGN KEY(strategy_record_id) REFERENCES strategy_records(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_paper_strategy_activations_active
                ON paper_strategy_activations(active, symbol, interval)
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

    def activate_paper(
        self,
        *,
        strategy_record_id: int,
        report_id: str = "",
        symbol: str,
        interval: str,
        warnings: list[str] | None = None,
    ) -> PaperActivation:
        if self.get_strategy(strategy_record_id) is None:
            raise ValueError("Strateji kaydı bulunamadı.")
        now = _utc_now_iso()
        uid = str(uuid.uuid4())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO paper_strategy_activations (
                    uid, strategy_record_id, report_id, symbol, interval,
                    active, created_at, updated_at, warnings_json
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                [
                    uid,
                    int(strategy_record_id),
                    report_id,
                    symbol.upper().strip(),
                    interval,
                    now,
                    now,
                    _stable_json(warnings or []),
                ],
            )
            activation_id = int(cursor.lastrowid)
        return PaperActivation(
            id=activation_id,
            uid=uid,
            strategy_record_id=int(strategy_record_id),
            report_id=report_id,
            symbol=symbol.upper().strip(),
            interval=interval,
            active=True,
            created_at=now,
            updated_at=now,
            warnings=list(warnings or []),
        )

    def deactivate_paper(self, activation_id: int) -> bool:
        now = _utc_now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE paper_strategy_activations
                SET active = 0, updated_at = ?
                WHERE id = ?
                """,
                [now, int(activation_id)],
            )
        return bool(cursor.rowcount)

    def list_paper_activations(self, active_only: bool = False) -> list[PaperActivation]:
        sql = "SELECT * FROM paper_strategy_activations"
        args: list[Any] = []
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY updated_at DESC, id DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._row_to_activation(row) for row in rows]

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

    @staticmethod
    def _row_to_activation(row: sqlite3.Row) -> PaperActivation:
        return PaperActivation(
            id=int(row["id"]),
            uid=str(row["uid"]),
            strategy_record_id=int(row["strategy_record_id"]),
            report_id=str(row["report_id"]),
            symbol=str(row["symbol"]),
            interval=str(row["interval"]),
            active=bool(row["active"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            warnings=json.loads(row["warnings_json"]),
        )

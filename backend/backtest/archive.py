"""Backtest rapor arşivi.

Raporlar JSON olarak saklanır; listeleme için temel indeks alanları ayrı
kolonlarda tutulur. SQLite seçimi bilerek basit: lokalde tek kullanıcı ve audit
trail için yeterli, ayrıca mevcut proje persistence tarzıyla uyumlu.
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class BacktestArchive:
    SCHEMA = """
        CREATE TABLE IF NOT EXISTS backtest_reports (
            id            TEXT PRIMARY KEY,
            created_at    TEXT NOT NULL,
            symbol        TEXT NOT NULL,
            interval      TEXT NOT NULL,
            strategy_id   TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            source_mode   TEXT NOT NULL,
            start_ts      INTEGER,
            end_ts        INTEGER,
            final_equity  REAL NOT NULL,
            return_pct    REAL NOT NULL,
            report_json   TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_backtest_reports_created
            ON backtest_reports(created_at DESC);
    """

    def __init__(self, db_path: str | Path) -> None:
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
        try:
            yield conn
        finally:
            conn.close()

    def save(self, report: dict[str, Any]) -> str:
        run_id = str(report.get("run_id") or uuid.uuid4())
        report = dict(report)
        report["run_id"] = run_id
        metrics = report.get("metrics", {})
        date_range = report.get("date_range", {})
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO backtest_reports (
                    id, created_at, symbol, interval, strategy_id, strategy_name,
                    source_mode, start_ts, end_ts, final_equity, return_pct, report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(report.get("generated_at", "")),
                    str(report.get("symbol", "")),
                    str(report.get("interval", "")),
                    str(report.get("strategy_id", "")),
                    str(report.get("strategy_name", "")),
                    str(report.get("source_mode", "")),
                    date_range.get("start"),
                    date_range.get("end"),
                    float(metrics.get("final_equity", 0.0)),
                    float(metrics.get("total_return_pct", 0.0)),
                    json.dumps(report, ensure_ascii=False, allow_nan=False),
                ),
            )
        return run_id

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, symbol, interval, strategy_id, strategy_name,
                       source_mode, start_ts, end_ts, final_equity, return_pct
                FROM backtest_reports
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_json FROM backtest_reports WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["report_json"]))


def trades_csv(report: dict[str, Any]) -> str:
    return _rows_csv(
        report.get("trades", []),
        [
            "symbol",
            "side",
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "quantity",
            "net_pnl",
            "return_pct",
            "commission",
            "slippage_cost",
        ],
    )


def equity_csv(report: dict[str, Any]) -> str:
    return _rows_csv(
        report.get("equity_curve", []),
        ["time", "bar_index", "cash", "position_value", "total_equity", "drawdown"],
    )


def _rows_csv(rows: list[dict[str, Any]], fields: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

"""Paper trading SQLite şeması ve veri erişim katmanı (Sprint 4.1)."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

_DEFAULT_DB = "data/cache/ohlcv.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trades (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id   TEXT    NOT NULL,
    symbol        TEXT    NOT NULL,
    side          TEXT    NOT NULL,
    price         REAL    NOT NULL,
    quantity      REAL    NOT NULL,
    commission    REAL    NOT NULL DEFAULT 0.0,
    pnl           REAL,
    opened_at     TEXT    NOT NULL,
    closed_at     TEXT,
    reason        TEXT
);
CREATE TABLE IF NOT EXISTS paper_portfolio (
    strategy_id      TEXT PRIMARY KEY,
    cash             REAL NOT NULL DEFAULT 10000.0,
    initial_capital  REAL NOT NULL DEFAULT 10000.0,
    daily_loss       REAL NOT NULL DEFAULT 0.0,
    daily_reset_date TEXT NOT NULL,
    is_halted        INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS paper_equity_curve (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id      TEXT NOT NULL,
    ts               TEXT NOT NULL,
    total_equity     REAL NOT NULL,
    cash             REAL NOT NULL,
    positions_value  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paper_trades_strategy
    ON paper_trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_paper_equity_strategy_ts
    ON paper_equity_curve(strategy_id, ts);
"""


class PaperDB:
    def __init__(self, db_path: str | Path = _DEFAULT_DB) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(str(self._path), timeout=10)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ── Wallet ────────────────────────────────────────────────────────────

    def get_or_create_wallet(self, strategy_id: str) -> dict[str, Any]:
        import datetime as dt
        today = dt.date.today().isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM paper_portfolio WHERE strategy_id = ?",
                (strategy_id,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO paper_portfolio (strategy_id, cash, initial_capital, "
                    "daily_loss, daily_reset_date, is_halted) VALUES (?,10000.0,10000.0,0.0,?,0)",
                    (strategy_id, today),
                )
                return {
                    "strategy_id": strategy_id,
                    "cash": 10000.0,
                    "initial_capital": 10000.0,
                    "daily_loss": 0.0,
                    "daily_reset_date": today,
                    "is_halted": 0,
                }
            return dict(row)

    def update_wallet(
        self,
        strategy_id: str,
        cash: float,
        daily_loss: float,
        daily_reset_date: str,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE paper_portfolio SET cash=?, daily_loss=?, daily_reset_date=? "
                "WHERE strategy_id=?",
                (cash, daily_loss, daily_reset_date, strategy_id),
            )

    def halt_strategy(self, strategy_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE paper_portfolio SET is_halted=1 WHERE strategy_id=?",
                (strategy_id,),
            )

    def resume_strategy(self, strategy_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE paper_portfolio SET is_halted=0 WHERE strategy_id=?",
                (strategy_id,),
            )

    def reset_wallet(self, strategy_id: str) -> None:
        import datetime as dt
        today = dt.date.today().isoformat()
        with self._conn() as conn:
            conn.execute(
                "UPDATE paper_portfolio SET cash=10000.0, daily_loss=0.0, "
                "is_halted=0, daily_reset_date=? WHERE strategy_id=?",
                (today, strategy_id),
            )
            conn.execute(
                "UPDATE paper_trades SET closed_at=?, pnl=0 "
                "WHERE strategy_id=? AND closed_at IS NULL",
                (dt.datetime.now(dt.timezone.utc).isoformat(), strategy_id),
            )

    def all_wallets(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM paper_portfolio").fetchall()
            return [dict(r) for r in rows]

    # ── Trades ────────────────────────────────────────────────────────────

    def record_trade(
        self,
        strategy_id: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        commission: float,
        opened_at: str,
        reason: str = "",
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO paper_trades (strategy_id, symbol, side, price, quantity, "
                "commission, opened_at, reason) VALUES (?,?,?,?,?,?,?,?)",
                (strategy_id, symbol, side, price, quantity, commission, opened_at, reason),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def close_trade(self, trade_id: int, price: float, pnl: float, closed_at: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE paper_trades SET closed_at=?, pnl=? WHERE id=?",
                (closed_at, pnl, trade_id),
            )

    def get_open_trade(self, strategy_id: str, symbol: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM paper_trades WHERE strategy_id=? AND symbol=? "
                "AND closed_at IS NULL ORDER BY id DESC LIMIT 1",
                (strategy_id, symbol),
            ).fetchone()
            return dict(row) if row else None

    def get_trades(self, strategy_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if strategy_id:
                rows = conn.execute(
                    "SELECT * FROM paper_trades WHERE strategy_id=? ORDER BY id DESC LIMIT ?",
                    (strategy_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM paper_trades ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def export_trades(self, strategy_id: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if strategy_id:
                rows = conn.execute(
                    "SELECT * FROM paper_trades WHERE strategy_id=? ORDER BY id DESC",
                    (strategy_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM paper_trades ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    # ── Equity curve ─────────────────────────────────────────────────────

    def record_equity_snapshot(
        self,
        strategy_id: str,
        ts: str,
        total_equity: float,
        cash: float,
        positions_value: float,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO paper_equity_curve (strategy_id, ts, total_equity, cash, "
                "positions_value) VALUES (?,?,?,?,?)",
                (strategy_id, ts, total_equity, cash, positions_value),
            )

    def get_equity_curve(self, strategy_id: str, limit: int = 200) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM paper_equity_curve WHERE strategy_id=? "
                "ORDER BY id DESC LIMIT ?",
                (strategy_id, limit),
            ).fetchall()
            return list(reversed([dict(r) for r in rows]))

    def checkpoint(self) -> None:
        """WAL modunda biriken sayfaları ana dosyaya yaz (graceful shutdown için)."""
        with self._lock:
            conn = sqlite3.connect(str(self._path), timeout=10)
            try:
                conn.execute("PRAGMA wal_checkpoint(FULL)")
                conn.commit()
            finally:
                conn.close()

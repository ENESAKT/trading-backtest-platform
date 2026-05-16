"""
SQLite Connection Pool — thread-safe bağlantı havuzu.

Python'un sqlite3 modülü thread-safe olmadığından,
her thread için ayrı bağlantı oluşturup yeniden kullanıyoruz.

Kullanım:
    pool = SQLitePool("data/paper.db", max_connections=8)
    with pool.connection() as conn:
        conn.execute("SELECT ...")

Health endpoint için pool.stats() çağrılır.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

_logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Pool durum istatistikleri."""
    db_path: str
    max_connections: int
    active_connections: int
    idle_connections: int
    total_checkouts: int
    total_checkins: int
    created_at: str
    uptime_seconds: float


@dataclass
class SQLitePool:
    """Thread-local SQLite connection pool.

    Her thread kendi bağlantısını tutar — WAL modu varsayılandır.
    """

    db_path: str | Path
    max_connections: int = 8
    wal_mode: bool = True
    _local: threading.local = field(default_factory=threading.local, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _connections: dict[int, sqlite3.Connection] = field(default_factory=dict, init=False, repr=False)
    _total_checkouts: int = field(default=0, init=False, repr=False)
    _total_checkins: int = field(default=0, init=False, repr=False)
    _created_at: float = field(default_factory=time.time, init=False, repr=False)

    def __post_init__(self) -> None:
        self.db_path = str(self.db_path)
        # DB dosyasının parent dizinini oluştur
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _create_connection(self) -> sqlite3.Connection:
        """Yeni SQLite bağlantısı oluştur."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA cache_size=-8000")  # 8MB
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Thread-local bağlantı al, işlem bitince havuza geri döndür."""
        tid = threading.get_ident()
        conn = getattr(self._local, "conn", None)

        if conn is None:
            with self._lock:
                if len(self._connections) >= self.max_connections:
                    # En eski bağlantıyı yeniden kullan
                    _logger.warning("[pool] Max connection limitine ulaşıldı: %d", self.max_connections)
                conn = self._create_connection()
                self._connections[tid] = conn
            self._local.conn = conn

        with self._lock:
            self._total_checkouts += 1

        try:
            yield conn
        finally:
            with self._lock:
                self._total_checkins += 1

    def close_all(self) -> None:
        """Tüm bağlantıları kapat."""
        with self._lock:
            for tid, conn in self._connections.items():
                try:
                    conn.close()
                except Exception:
                    pass
            self._connections.clear()
            self._local.conn = None

    def stats(self) -> PoolStats:
        """Pool istatistiklerini döndür."""
        with self._lock:
            active = self._total_checkouts - self._total_checkins
            return PoolStats(
                db_path=self.db_path,
                max_connections=self.max_connections,
                active_connections=max(0, active),
                idle_connections=len(self._connections) - max(0, active),
                total_checkouts=self._total_checkouts,
                total_checkins=self._total_checkins,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._created_at)),
                uptime_seconds=round(time.time() - self._created_at, 1),
            )

    def stats_dict(self) -> dict:
        """Health endpoint için dict formatında istatistikler."""
        s = self.stats()
        return {
            "db_path": s.db_path,
            "max_connections": s.max_connections,
            "active": s.active_connections,
            "idle": s.idle_connections,
            "total_checkouts": s.total_checkouts,
            "uptime_seconds": s.uptime_seconds,
        }

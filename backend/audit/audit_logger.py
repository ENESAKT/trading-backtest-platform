"""
audit_logger.py — Uygulama genelinde denetim logu sistemi.

Para veya karar etkisi olan her olay bu modül üzerinden loglanır:
  - Kullanıcı auth olayları (login, logout, token yenileme)
  - Plan değişiklik olayları (upgrade, downgrade, trial start)
  - Backtest çalıştırma
  - Screener çalıştırma
  - Sinyal üretimi (uyarı niteliğindekiler)
  - Paper emir/fill
  - Admin aksiyonu (rol değişikliği, kullanıcı engeli)
  - Provider değişimi (sessiz failover uyarısı)
  - Veri kalite blokları

Depolama önceliği:
  1. MySQL `audit_log` tablosu (production)
  2. SQLite fallback (yerel geliştirme, MySQL yoksa)
  3. Structured log (tüm ortamlar, en az garanti)

Kullanım:
    from backend.audit import audit_logger, AuditEvent

    await audit_logger.log(AuditEvent(
        action="backtest_run",
        user_id=42,
        resource="THYAO.IS/1d",
        metadata={"strategy": "rsi_cross", "bars": 250},
    ))

    # Request'ten IP al (FastAPI):
    audit_logger.log_sync(AuditEvent(...), ip=request.client.host)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

# ─── Sabitler ────────────────────────────────────────────────────────────────

# Bilinen aksiyon kategorileri (açık liste — extensible)
class AuditAction:
    # Auth
    AUTH_LOGIN          = "auth_login"
    AUTH_LOGOUT         = "auth_logout"
    AUTH_REGISTER       = "auth_register"
    AUTH_TOKEN_REFRESH  = "auth_token_refresh"
    AUTH_PW_RESET       = "auth_password_reset"
    AUTH_EMAIL_VERIFY   = "auth_email_verify"
    AUTH_FAILED_LOGIN   = "auth_failed_login"

    # Plan / abonelik
    PLAN_UPGRADE        = "plan_upgrade"
    PLAN_DOWNGRADE      = "plan_downgrade"
    PLAN_TRIAL_START    = "plan_trial_start"
    PLAN_CANCEL         = "plan_cancel"
    PLAN_PAYMENT_OK     = "plan_payment_ok"
    PLAN_PAYMENT_FAIL   = "plan_payment_fail"

    # Backtest / strateji
    BACKTEST_RUN        = "backtest_run"
    BACKTEST_SAVE       = "backtest_save"
    BACKTEST_DELETE     = "backtest_delete"
    BACKTEST_SHARE      = "backtest_share"

    # Screener
    SCREENER_RUN        = "screener_run"

    # Sinyaller
    SIGNAL_EMIT         = "signal_emit"
    SIGNAL_BLOCK        = "signal_block"

    # Paper trading
    PAPER_ORDER_SUBMIT  = "paper_order_submit"
    PAPER_ORDER_FILL    = "paper_order_fill"
    PAPER_ORDER_CANCEL  = "paper_order_cancel"
    PAPER_RESET         = "paper_reset"

    # Fiyat alarmları
    ALERT_CREATE        = "alert_create"
    ALERT_TRIGGER       = "alert_trigger"
    ALERT_DELETE        = "alert_delete"

    # Admin
    ADMIN_ROLE_CHANGE   = "admin_role_change"
    ADMIN_USER_BAN      = "admin_user_ban"
    ADMIN_USER_ACTIVATE = "admin_user_activate"
    ADMIN_QUOTA_RESET   = "admin_quota_reset"

    # Veri / provider
    PROVIDER_SWITCH     = "provider_switch"
    DATA_QUALITY_BLOCK  = "data_quality_block"
    RETENTION_EXECUTE   = "retention_execute"
    DATA_EXPORT         = "data_export"


# ─── AuditEvent ──────────────────────────────────────────────────────────────

@dataclass
class AuditEvent:
    """Tek bir denetim olayını temsil eder."""
    action: str                             # AuditAction sabitlerinden biri
    user_id: int | None = None              # Oturum sahibi (yoksa None)
    resource: str | None = None            # Etkilenen kaynak (sembol, endpoint, vb.)
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─── AuditLogger ─────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Audit olaylarını MySQL veya SQLite'a (fallback) yazar.

    Thread-safe; SQLite kilidini threading.Lock ile korur.
    MySQL için aiomysql connection pool beklenir (inject edilir).
    """

    def __init__(self) -> None:
        self._pool = None            # aiomysql pool (set_pool ile inject edilir)
        self._sqlite_path: Path | None = None
        self._sqlite_lock = threading.Lock()
        self._use_mysql = False
        self._initialized = False

    def configure(
        self,
        *,
        mysql_pool=None,
        sqlite_path: str | Path | None = None,
    ) -> None:
        """
        Depolama backend'ini yapılandır.
        mysql_pool önceliklidir; yoksa sqlite_path kullanılır.
        """
        if mysql_pool is not None:
            self._pool = mysql_pool
            self._use_mysql = True
            _logger.info("[AuditLogger] MySQL pool yapılandırıldı.")
        elif sqlite_path:
            self._sqlite_path = Path(sqlite_path)
            self._use_mysql = False
            self._ensure_sqlite()
            _logger.info("[AuditLogger] SQLite fallback: %s", self._sqlite_path)
        self._initialized = True

    def set_pool(self, pool) -> None:
        """MySQL pool'u inject et (FastAPI lifespan'dan)."""
        self._pool = pool
        self._use_mysql = True
        self._initialized = True

    # ─── SQLite init ─────────────────────────────────────────────────────────

    def _ensure_sqlite(self) -> None:
        if not self._sqlite_path:
            return
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._sqlite_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER,
                    action     TEXT NOT NULL,
                    resource   TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    metadata   TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_al_action ON audit_log(action)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_al_user_id ON audit_log(user_id)")
            conn.commit()

    # ─── Async write (MySQL) ─────────────────────────────────────────────────

    async def log(self, event: AuditEvent) -> None:
        """Olayı async olarak yaz. Hata olursa structured log'a düşer."""
        # Her zaman structured log
        _logger.info(
            "[AUDIT] action=%s user_id=%s resource=%s ip=%s meta=%s",
            event.action, event.user_id, event.resource,
            event.ip_address, json.dumps(event.metadata, ensure_ascii=False),
        )

        if self._use_mysql and self._pool:
            await self._write_mysql(event)
        elif self._sqlite_path:
            self._write_sqlite(event)
        # else: sadece log (no-op on storage)

    async def _write_mysql(self, event: AuditEvent) -> None:
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO audit_log
                           (user_id, action, resource, ip_address, user_agent, metadata, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (
                            event.user_id,
                            event.action[:100],
                            (event.resource or "")[:200],
                            (event.ip_address or "")[:45],
                            (event.user_agent or "")[:500],
                            json.dumps(event.metadata, ensure_ascii=False, default=str),
                            event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                await conn.commit()
        except Exception as exc:  # noqa: BLE001
            _logger.warning("[AuditLogger] MySQL yazımı başarısız, SQLite fallback: %s", exc)
            self._write_sqlite(event)

    # ─── Sync write (SQLite fallback) ────────────────────────────────────────

    def _write_sqlite(self, event: AuditEvent) -> None:
        if not self._sqlite_path:
            return
        try:
            with self._sqlite_lock:
                with sqlite3.connect(self._sqlite_path) as conn:
                    conn.execute(
                        """INSERT INTO audit_log
                           (user_id, action, resource, ip_address, user_agent, metadata, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            event.user_id,
                            event.action[:100],
                            (event.resource or "")[:200],
                            (event.ip_address or "")[:45],
                            (event.user_agent or "")[:500],
                            json.dumps(event.metadata, ensure_ascii=False, default=str),
                            event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                    conn.commit()
        except Exception as exc:  # noqa: BLE001
            _logger.error("[AuditLogger] SQLite yazımı da başarısız: %s", exc)

    def log_sync(self, event: AuditEvent) -> None:
        """
        Senkron bağlamlarda kullanım için (signal handler, celery vb.).
        MySQL için fire-and-forget asyncio task oluşturmaz — sadece SQLite/log yazar.
        """
        _logger.info(
            "[AUDIT] action=%s user_id=%s resource=%s",
            event.action, event.user_id, event.resource,
        )
        if self._sqlite_path:
            self._write_sqlite(event)

    # ─── Sorgulama ───────────────────────────────────────────────────────────

    async def query(
        self,
        *,
        user_id: int | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Audit loglarını sorgular (MySQL veya SQLite)."""
        limit = max(1, min(limit, 500))
        if self._use_mysql and self._pool:
            return await self._query_mysql(user_id=user_id, action=action, limit=limit, offset=offset)
        return self._query_sqlite(user_id=user_id, action=action, limit=limit, offset=offset)

    async def _query_mysql(self, *, user_id, action, limit, offset) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if user_id is not None:
            clauses.append("user_id=%s")
            params.append(user_id)
        if action:
            clauses.append("action=%s")
            params.append(action)
        params.extend([limit, offset])
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"""SELECT id, user_id, action, resource, ip_address, metadata, created_at
                            FROM audit_log WHERE {' AND '.join(clauses)}
                            ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                        params,
                    )
                    rows = await cur.fetchall()
            return [
                {
                    "id": r[0], "user_id": r[1], "action": r[2],
                    "resource": r[3], "ip_address": r[4],
                    "metadata": r[5], "created_at": str(r[6]),
                }
                for r in rows
            ]
        except Exception as exc:  # noqa: BLE001
            _logger.warning("[AuditLogger] MySQL sorgu başarısız: %s", exc)
            return []

    def _query_sqlite(self, *, user_id, action, limit, offset) -> list[dict[str, Any]]:
        if not self._sqlite_path or not self._sqlite_path.exists():
            return []
        clauses = ["1=1"]
        params: list[Any] = []
        if user_id is not None:
            clauses.append("user_id=?")
            params.append(user_id)
        if action:
            clauses.append("action=?")
            params.append(action)
        params.extend([limit, offset])
        try:
            with self._sqlite_lock:
                with sqlite3.connect(self._sqlite_path) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        f"""SELECT id, user_id, action, resource, ip_address, metadata, created_at
                            FROM audit_log WHERE {' AND '.join(clauses)}
                            ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                        params,
                    ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            _logger.error("[AuditLogger] SQLite sorgu başarısız: %s", exc)
            return []


# ─── Singleton ───────────────────────────────────────────────────────────────

def _resolve_default_sqlite() -> Path | None:
    """
    Varsayılan SQLite yolunu çözer.
    Env var yoksa proje db/ dizinini dener; yazılamazsa /tmp/ kullanır.
    """
    env_path = os.environ.get("AUDIT_LOG_SQLITE")
    if env_path:
        return Path(env_path)
    # Proje db/ dizini
    candidate = Path(os.path.dirname(__file__)) / "../../db/audit_log.db"
    candidate = candidate.resolve()
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        # Yazılabilirlik testi
        test_file = candidate.parent / ".audit_write_test"
        test_file.touch()
        test_file.unlink()
        return candidate
    except Exception:
        # Fallback: /tmp
        return Path("/tmp/piyasapilot_audit_log.db")


audit_logger = AuditLogger()
_sqlite_path = _resolve_default_sqlite()
if _sqlite_path:
    audit_logger.configure(sqlite_path=_sqlite_path)

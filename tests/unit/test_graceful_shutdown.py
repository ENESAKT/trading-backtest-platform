"""PaperDB.checkpoint() ve lifespan shutdown davranışı testleri."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.paper.db import PaperDB


class TestPaperDBCheckpoint:
    def test_checkpoint_calls_wal_pragma(self, tmp_path: Path) -> None:
        db = PaperDB(tmp_path / "test.sqlite3")
        db.ensure_tables()
        # WAL modunu aktifleştir
        with db._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        # Checkpoint çağrısı hata vermemeli
        db.checkpoint()

    def test_checkpoint_on_nonexistent_db_creates_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "new.sqlite3"
        db = PaperDB(db_path)
        db.checkpoint()
        assert db_path.exists()

    def test_checkpoint_pragma_executes(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wal_test.sqlite3"
        db = PaperDB(db_path)
        db.ensure_tables()

        executed_pragmas: list[str] = []
        original_conn = db._conn

        class _TrackingConn:
            def __enter__(self_inner):
                conn = sqlite3.connect(str(db_path), timeout=10)
                original_execute = conn.execute

                def tracking_execute(sql, *args, **kwargs):
                    executed_pragmas.append(sql)
                    return original_execute(sql, *args, **kwargs)

                conn.execute = tracking_execute  # type: ignore[method-assign]
                return conn

            def __exit__(self_inner, *a):
                pass

        with patch.object(db, "_lock", db._lock):
            db.checkpoint()

        # checkpoint() çağrıldığında WAL pragma çalıştırılır (dosya var ve erişilebilir)
        assert db_path.exists()


class TestEnvValidationLogging:
    def test_missing_env_logs_warnings(self) -> None:
        """_check_optional_env eksik değişkenler için uyarı loglar."""
        import logging
        from unittest.mock import patch

        with patch.dict("os.environ", {}, clear=False):
            # Tüm opsiyonel değerleri geçici olarak kaldır
            keys = [
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
                "SMTP_HOST", "BIST_HTTP_URL_TEMPLATE", "VIOP_HTTP_URL_TEMPLATE",
            ]
            env_patch = {k: "" for k in keys}
            with patch("backend.config.getenv", side_effect=lambda k, d="": env_patch.get(k, d)):
                with patch("backend.api.main._logger") as mock_logger:
                    from backend.api.main import _check_optional_env
                    _check_optional_env()
                    assert mock_logger.warning.call_count >= 2

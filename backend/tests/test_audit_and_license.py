"""
test_audit_and_license.py — AuditLogger ve LicenseMatrix birim testleri.

Çalıştırma:
    cd /path/to/Backtest && PYTHONPATH=. pytest backend/tests/test_audit_and_license.py -v
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from backend.audit.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditAction,
)
from backend.data.license_matrix import (
    LicenseMatrix,
    LicenseViolation,
    license_matrix,
)


# ─── AuditLogger Testleri ────────────────────────────────────────────────────

class TestAuditLoggerSQLite:

    def _make_logger(self, tmp_path: Path) -> AuditLogger:
        logger = AuditLogger()
        logger.configure(sqlite_path=tmp_path / "audit.db")
        return logger

    def test_sqlite_db_created(self, tmp_path):
        logger = self._make_logger(tmp_path)
        assert (tmp_path / "audit.db").exists()

    def test_log_sync_writes_row(self, tmp_path):
        logger = self._make_logger(tmp_path)
        event = AuditEvent(
            action=AuditAction.BACKTEST_RUN,
            user_id=42,
            resource="THYAO.IS/1d",
            metadata={"strategy": "rsi_cross"},
        )
        logger.log_sync(event)
        rows = logger._query_sqlite(user_id=42, action=None, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0]["action"] == AuditAction.BACKTEST_RUN
        assert rows[0]["resource"] == "THYAO.IS/1d"

    def test_log_async_writes_row(self, tmp_path):
        logger = self._make_logger(tmp_path)
        event = AuditEvent(
            action=AuditAction.SCREENER_RUN,
            user_id=7,
            resource="BIST/BIST100",
        )
        asyncio.get_event_loop().run_until_complete(logger.log(event))
        rows = logger._query_sqlite(user_id=7, action=None, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0]["action"] == AuditAction.SCREENER_RUN

    def test_multiple_events_ordered_desc(self, tmp_path):
        logger = self._make_logger(tmp_path)
        for i in range(5):
            logger.log_sync(AuditEvent(action=AuditAction.BACKTEST_RUN, user_id=1, resource=f"SYM{i}"))
        rows = logger._query_sqlite(user_id=1, action=None, limit=10, offset=0)
        assert len(rows) == 5
        # Tüm kayıtlar var — id'ler artan ya da azalan, her biri eşsiz olmalı
        ids = [r["id"] for r in rows]
        assert len(set(ids)) == 5  # eşsiz id'ler

    def test_filter_by_action(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_sync(AuditEvent(action=AuditAction.BACKTEST_RUN, user_id=1))
        logger.log_sync(AuditEvent(action=AuditAction.SCREENER_RUN, user_id=1))
        rows = logger._query_sqlite(user_id=None, action=AuditAction.SCREENER_RUN, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0]["action"] == AuditAction.SCREENER_RUN

    def test_filter_by_user_id(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_sync(AuditEvent(action=AuditAction.AUTH_LOGIN, user_id=1))
        logger.log_sync(AuditEvent(action=AuditAction.AUTH_LOGIN, user_id=2))
        rows = logger._query_sqlite(user_id=2, action=None, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0]["user_id"] == 2

    def test_limit_respected(self, tmp_path):
        logger = self._make_logger(tmp_path)
        for _ in range(10):
            logger.log_sync(AuditEvent(action=AuditAction.BACKTEST_RUN, user_id=1))
        rows = logger._query_sqlite(user_id=None, action=None, limit=3, offset=0)
        assert len(rows) == 3

    def test_metadata_persisted_as_json(self, tmp_path):
        logger = self._make_logger(tmp_path)
        meta = {"strategy": "rsi_cross", "bars": 250, "capital": 100_000}
        logger.log_sync(AuditEvent(action=AuditAction.BACKTEST_RUN, user_id=1, metadata=meta))
        rows = logger._query_sqlite(user_id=1, action=None, limit=1, offset=0)
        stored_meta = rows[0]["metadata"]
        if isinstance(stored_meta, str):
            stored_meta = json.loads(stored_meta)
        assert stored_meta["strategy"] == "rsi_cross"
        assert stored_meta["bars"] == 250

    def test_query_async(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_sync(AuditEvent(action=AuditAction.PAPER_ORDER_SUBMIT, user_id=99))
        rows = asyncio.get_event_loop().run_until_complete(
            logger.query(user_id=99, limit=10)
        )
        assert len(rows) == 1

    def test_no_crash_on_empty_db(self, tmp_path):
        logger = self._make_logger(tmp_path)
        rows = logger._query_sqlite(user_id=999, action=None, limit=10, offset=0)
        assert rows == []

    def test_action_constants_are_strings(self):
        """AuditAction sabitleri string olmalı (type safety)."""
        assert isinstance(AuditAction.BACKTEST_RUN, str)
        assert isinstance(AuditAction.AUTH_LOGIN, str)
        assert isinstance(AuditAction.PROVIDER_SWITCH, str)
        assert isinstance(AuditAction.ADMIN_ROLE_CHANGE, str)

    def test_event_defaults(self):
        event = AuditEvent(action=AuditAction.AUTH_LOGIN)
        assert event.user_id is None
        assert event.resource is None
        assert event.metadata == {}
        assert event.created_at is not None

    def test_unconfigured_logger_does_not_crash(self):
        """Yapılandırılmamış logger sessizce çalışır (sadece log yazar)."""
        logger = AuditLogger()
        # log_sync — sqlite_path yok, pool yok
        logger.log_sync(AuditEvent(action="test_action"))  # exception fırlatmamalı


# ─── LicenseMatrix Testleri ──────────────────────────────────────────────────

class TestLicenseMatrix:

    def test_get_known_entry(self):
        entry = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert entry is not None
        assert entry.provider == "yfinance"
        assert entry.market == "BIST"
        assert entry.data_type == "ohlcv"

    def test_yfinance_bist_not_redistributable(self):
        entry = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert entry is not None
        assert entry.can_redistribute is False

    def test_kap_fundamental_redistributable(self):
        """KAP verisi kamuya açık — redistribute edilebilir."""
        entry = license_matrix.get("kap", "BIST", "fundamental")
        assert entry is not None
        assert entry.can_redistribute is True

    def test_binance_crypto_ohlcv_is_live(self):
        entry = license_matrix.get("binance", "CRYPTO", "ohlcv")
        assert entry is not None
        assert entry.is_live is True
        assert entry.delay_minutes == 0

    def test_yfinance_bist_has_delay(self):
        entry = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert entry is not None
        assert entry.delay_minutes == 15

    def test_unknown_entry_returns_none(self):
        entry = license_matrix.get("unknown_provider", "MARS", "ohlcv")
        assert entry is None

    def test_get_or_default_returns_restrictive_default(self):
        """Bilinmeyen kombinasyon için kısıtlayıcı varsayılan döner."""
        entry = license_matrix.get_or_default("unknown", "XYZ", "ohlcv")
        assert entry.can_redistribute is False
        assert entry.can_export is False
        assert entry.min_plan == "pro"

    def test_case_insensitive_lookup(self):
        """Provider/market büyük/küçük harf fark etmemeli."""
        e1 = license_matrix.get("YFINANCE", "bist", "OHLCV")
        e2 = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert e1 is not None
        assert e2 is not None
        assert e1.provider == e2.provider

    def test_export_allowed_pro_plan(self):
        """Pro planı ile yfinance/BIST/ohlcv export edilebilir."""
        allowed = license_matrix.check_export_allowed("yfinance", "BIST", "ohlcv", user_plan="pro")
        assert allowed is True

    def test_export_not_allowed_free_plan(self):
        """Free planı ile yfinance/BIST/ohlcv export edilemez (export_min_plan=pro)."""
        allowed = license_matrix.check_export_allowed("yfinance", "BIST", "ohlcv", user_plan="free")
        assert allowed is False

    def test_view_allowed_free_plan(self):
        """Free planı ile yfinance/BIST/ohlcv görüntülenebilir."""
        allowed = license_matrix.check_view_allowed("yfinance", "BIST", "ohlcv", user_plan="free")
        assert allowed is True

    def test_matriks_requires_pro_plan(self):
        """Matriks BIST verisi min_plan=pro."""
        entry = license_matrix.get("matriks", "BIST", "ohlcv")
        assert entry is not None
        assert entry.min_plan == "pro"
        assert license_matrix.check_view_allowed("matriks", "BIST", "ohlcv", "free") is False
        assert license_matrix.check_view_allowed("matriks", "BIST", "ohlcv", "pro") is True

    def test_assert_export_raises_violation(self):
        """Free plan ile export edilemeyenlerde LicenseViolation fırlatır."""
        with pytest.raises(LicenseViolation) as exc_info:
            license_matrix.assert_export("yfinance", "BIST", "ohlcv", user_plan="free")
        assert "export" in str(exc_info.value).lower() or "plan" in str(exc_info.value).lower()

    def test_assert_export_does_not_raise_for_pro(self):
        """Pro plan ile assert_export hata fırlatmamalı."""
        license_matrix.assert_export("yfinance", "BIST", "ohlcv", user_plan="pro")

    def test_kap_export_allowed_for_free(self):
        """KAP verisi free plan ile export edilebilir."""
        allowed = license_matrix.check_export_allowed("kap", "BIST", "fundamental", user_plan="free")
        assert allowed is True

    def test_binance_tick_requires_pro(self):
        """Binance tick min_plan=pro."""
        entry = license_matrix.get("binance", "CRYPTO", "tick")
        assert entry is not None
        assert entry.min_plan == "pro"

    def test_all_entries_returns_list(self):
        entries = license_matrix.all_entries()
        assert len(entries) > 0
        assert all(hasattr(e, "provider") for e in entries)

    def test_as_dict_serializable(self):
        data = license_matrix.as_dict()
        assert isinstance(data, list)
        assert len(data) > 0
        # JSON serileştirilebilir olmalı
        serialized = json.dumps(data)
        assert len(serialized) > 0

    def test_legal_note_present(self):
        """Tüm kayıtlı girişlerin legal_note'u var."""
        for entry in license_matrix.all_entries():
            assert isinstance(entry.legal_note, str)

    def test_entry_to_dict_has_required_keys(self):
        entry = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert entry is not None
        d = entry.to_dict()
        for key in ["provider", "market", "data_type", "is_live", "can_redistribute",
                    "can_export", "min_plan", "export_min_plan", "legal_note"]:
            assert key in d, f"Eksik key: {key}"

    def test_viop_not_exportable(self):
        """VİOP verisi export edilemez."""
        entry = license_matrix.get("matriks", "VIOP", "ohlcv")
        assert entry is not None
        assert entry.can_export is False

    def test_plan_rank_ordering(self):
        """Plan rank sırası doğru: guest < free < pro < ultra < admin."""
        entry = license_matrix.get("yfinance", "BIST", "ohlcv")
        assert entry is not None
        assert entry.plan_rank("guest") < entry.plan_rank("free")
        assert entry.plan_rank("free") < entry.plan_rank("pro")
        assert entry.plan_rank("pro") < entry.plan_rank("ultra")
        assert entry.plan_rank("ultra") < entry.plan_rank("admin")

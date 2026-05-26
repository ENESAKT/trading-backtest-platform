"""Unit testler: Retention sorgu güvenliği (RetentionManager).

Bölüm 18.14 — risk bazlı test kapsamı: retention query safety.

Test senaryoları:
  - apply_policy(execute=False) → dry-run, veri silinmemeli
  - apply_policy(execute=True) → gerçek silme, audit_id üretilmeli
  - Politika bulunamazsa varsayılan 30 gün kullanılmalı
  - dry_run → rows_to_delete alanı raporlanmalı
  - Silme sorgusunda cutoff ts < koşulu zorunlu (tüm tablo silme önlemi)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone

from backend.data.ingest.retention import RetentionManager, _DEFAULT_RETENTION_DAYS


# ─── Yardımcı mock'lar ───────────────────────────────────────────────────────

def _make_repos(policy=None, count=50):
    """ch_repo ve mysql_repo mock'larını döndürür."""
    # ClickHouse repo mock
    ch_repo = MagicMock()
    ch_repo.client = MagicMock()
    ch_repo.client.query.return_value.result_rows = [(count,)]
    ch_repo.client.command.return_value = None

    # MySQL repo mock — `async with self.mysql_repo.acquire() as conn:` yapısı
    # conn.cursor() → `async with conn.cursor() as cur:` yapısı
    if policy:
        row = (policy["retention_days"], policy.get("archive_before_delete", False))
    else:
        row = None

    # cursor context manager
    cur_mock = AsyncMock()
    cur_mock.execute = AsyncMock(return_value=None)
    cur_mock.fetchone = AsyncMock(return_value=row)

    # cursor() bir async context manager döndürmeli
    cursor_cm = AsyncMock()
    cursor_cm.__aenter__ = AsyncMock(return_value=cur_mock)
    cursor_cm.__aexit__ = AsyncMock(return_value=None)

    # connection context manager
    conn_mock = AsyncMock()
    conn_mock.cursor = MagicMock(return_value=cursor_cm)
    conn_mock.__aenter__ = AsyncMock(return_value=conn_mock)
    conn_mock.__aexit__ = AsyncMock(return_value=None)

    # acquire() bir async context manager döndürmeli
    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn_mock)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    mysql_repo = MagicMock()
    mysql_repo.acquire = MagicMock(return_value=acquire_cm)

    return ch_repo, mysql_repo


# ─── Testler ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestRetentionSafety:

    async def test_apply_policy_default_is_dryrun(self):
        """execute belirtilmezse varsayılan dry-run olmalı; silme yapılmamalı."""
        ch, my = _make_repos()
        mgr = RetentionManager(ch, my)

        result = await mgr.apply_policy(market="BIST", instrument_type="stock", timeframe="1m")

        assert result["dry_run"] is True
        ch.client.command.assert_not_called()

    async def test_apply_policy_execute_false_no_delete(self):
        """execute=False → hiçbir silme komutu çalışmamalı."""
        ch, my = _make_repos(count=200)
        mgr = RetentionManager(ch, my)

        result = await mgr.apply_policy(
            market="BIST", instrument_type="stock", timeframe="1m", execute=False
        )

        assert result["dry_run"] is True
        ch.client.command.assert_not_called()

    async def test_apply_policy_execute_true_produces_audit_id(self):
        """execute=True → audit_id üretilmeli ve silme komutu çağrılmalı."""
        ch, my = _make_repos(count=100)
        mgr = RetentionManager(ch, my)

        result = await mgr.apply_policy(
            market="BIST", instrument_type="stock", timeframe="1m", execute=True
        )

        assert result["dry_run"] is False
        assert "audit_id" in result
        assert len(result["audit_id"]) == 36  # UUID formatı
        ch.client.command.assert_called_once()

    async def test_apply_policy_execute_true_zero_rows_skips_delete(self):
        """Silinecek satır yoksa komut çağrılmamalı."""
        ch, my = _make_repos(count=0)
        mgr = RetentionManager(ch, my)

        result = await mgr.apply_policy(
            market="BIST", instrument_type="stock", timeframe="1m", execute=True
        )

        # count=0 ise _delete_rows erken döner
        ch.client.command.assert_not_called()
        assert result["rows_deleted"] == 0

    async def test_dry_run_reports_rows_to_delete(self):
        """dry_run → rows_to_delete doğru rapor edilmeli."""
        ch, my = _make_repos(count=999)
        mgr = RetentionManager(ch, my)

        result = await mgr.dry_run(market="BIST", instrument_type="stock", timeframe="1m")

        assert result["dry_run"] is True
        assert result["rows_to_delete"] == 999

    async def test_uses_policy_retention_days(self):
        """DB'deki politika retention_days kullanılmalı."""
        ch, my = _make_repos(policy={"retention_days": 90}, count=5)
        mgr = RetentionManager(ch, my)

        result = await mgr.dry_run(market="BIST", instrument_type="stock", timeframe="1d")

        assert result["retention_days"] == 90
        assert result["policy_found"] is True

    async def test_uses_default_when_no_policy(self):
        """Politika bulunamazsa _DEFAULT_RETENTION_DAYS kullanılmalı."""
        ch, my = _make_repos(policy=None, count=10)
        mgr = RetentionManager(ch, my)

        result = await mgr.dry_run(market="VIOP", instrument_type="future", timeframe="15m")

        assert result["retention_days"] == _DEFAULT_RETENTION_DAYS
        assert result["policy_found"] is False

    async def test_delete_query_contains_ts_cutoff(self):
        """Silme komutunun WHERE koşulunda 'ts <' ifadesi zorunlu (tüm tablo silme önlemi)."""
        ch, my = _make_repos(count=1)
        mgr = RetentionManager(ch, my)

        await mgr.apply_policy(
            market="BIST", instrument_type="stock", timeframe="1m", execute=True
        )

        cmd_args = ch.client.command.call_args
        query_str: str = cmd_args[0][0] if cmd_args[0] else ""
        assert "ts <" in query_str.lower() or "ts <" in query_str, (
            "Silme sorgusu 'ts <' (cutoff) koşulu içermeli!"
        )

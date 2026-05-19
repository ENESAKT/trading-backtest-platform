"""Veri saklama süresi (retention) motoru.

Kullanım:
    manager = RetentionManager(clickhouse_repo, mysql_pool)

    # Ne silineceğini gör (güvenli, veri değiştirmez):
    report = await manager.dry_run(market="BIST", instrument_type="stock", timeframe="1m")

    # Gerçekten sil (audit kaydı oluşturur):
    result = await manager.apply_policy(market="BIST", instrument_type="stock", timeframe="1m")

Güvenlik kuralları:
    - Dry-run onaylanmadan execute çalışmaz (execute=True gerekir).
    - Silme sorgusu WHERE ts < cutoff koşulunu kesinlikle içermelidir.
    - Her silme işlemi audit_id ile izlenir.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Politika bulunamazsa kullanılacak güvenli varsayılan (30 gün)
_DEFAULT_RETENTION_DAYS = 30


class RetentionManager:
    def __init__(self, clickhouse_repo, mysql_repo) -> None:
        self.ch_repo = clickhouse_repo
        self.mysql_repo = mysql_repo

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    async def _fetch_policy(
        self, market: str, instrument_type: str, timeframe: str
    ) -> dict[str, Any] | None:
        """MySQL'den retention policy getirir."""
        try:
            async with self.mysql_repo.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT retention_days, archive_before_delete
                        FROM data_retention_policy
                        WHERE market = %s AND instrument_type = %s AND timeframe = %s
                        LIMIT 1
                        """,
                        (market, instrument_type, timeframe),
                    )
                    row = await cur.fetchone()
                    if row:
                        return {"retention_days": row[0], "archive_before_delete": bool(row[1])}
        except Exception as exc:
            logger.warning("Retention policy okunamadı: %s", exc)
        return None

    def _compute_cutoff(self, retention_days: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=retention_days)

    async def _count_rows(
        self,
        market: str,
        symbol: str | None,
        instrument_type: str,
        timeframe: str,
        cutoff: datetime,
    ) -> int:
        """Silinecek satır sayısını ClickHouse'da say (değiştirmez)."""
        try:
            where_symbol = "AND symbol = {sym:String}" if symbol else ""
            sym_param = {"sym": symbol} if symbol else {}
            query = (
                f"SELECT count() FROM market_bars "
                f"WHERE market = {{market:String}} "
                f"AND instrument_type = {{itype:String}} "
                f"AND timeframe = {{tf:String}} "
                f"AND ts < {{cutoff:DateTime64(3,'UTC')}} "
                f"{where_symbol}"
            )
            params = {
                "market": market,
                "itype": instrument_type,
                "tf": timeframe,
                "cutoff": cutoff,
                **sym_param,
            }
            result = self.ch_repo.client.query(query, parameters=params)
            return int(result.result_rows[0][0]) if result.result_rows else 0
        except Exception as exc:
            logger.error("Retention count sorgusu başarısız: %s", exc)
            return -1

    async def _delete_rows(
        self,
        market: str,
        symbol: str | None,
        instrument_type: str,
        timeframe: str,
        cutoff: datetime,
        audit_id: str,
    ) -> int:
        """ClickHouse'dan eski satırları sil ve audit kaydı yaz."""
        count_before = await self._count_rows(market, symbol, instrument_type, timeframe, cutoff)
        if count_before == 0:
            return 0

        try:
            where_symbol = "AND symbol = {sym:String}" if symbol else ""
            sym_param = {"sym": symbol} if symbol else {}
            # ClickHouse lightweight delete (v23.3+)
            delete_query = (
                f"DELETE FROM market_bars "
                f"WHERE market = {{market:String}} "
                f"AND instrument_type = {{itype:String}} "
                f"AND timeframe = {{tf:String}} "
                f"AND ts < {{cutoff:DateTime64(3,'UTC')}} "
                f"{where_symbol}"
            )
            params = {
                "market": market,
                "itype": instrument_type,
                "tf": timeframe,
                "cutoff": cutoff,
                **sym_param,
            }
            self.ch_repo.client.command(delete_query, parameters=params)
            logger.info(
                "[%s] Retention silme tamamlandı: %s %s %s | ~%d satır | cutoff=%s",
                audit_id, market, instrument_type, timeframe, count_before, cutoff.isoformat(),
            )
            return count_before
        except Exception as exc:
            logger.error("[%s] Retention silme başarısız: %s", audit_id, exc)
            raise

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    async def dry_run(
        self,
        market: str,
        instrument_type: str,
        timeframe: str,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """Silinecek satır sayısını raporlar — hiçbir şeyi değiştirmez."""
        policy = await self._fetch_policy(market, instrument_type, timeframe)
        retention_days = policy["retention_days"] if policy else _DEFAULT_RETENTION_DAYS
        cutoff = self._compute_cutoff(retention_days)
        count = await self._count_rows(market, symbol, instrument_type, timeframe, cutoff)

        return {
            "dry_run": True,
            "market": market,
            "instrument_type": instrument_type,
            "timeframe": timeframe,
            "symbol": symbol,
            "retention_days": retention_days,
            "cutoff": cutoff.isoformat(),
            "rows_to_delete": count,
            "policy_found": policy is not None,
        }

    async def apply_policy(
        self,
        market: str,
        instrument_type: str,
        timeframe: str,
        symbol: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        """Retention politikasını uygular.

        Args:
            execute: True ise silme gerçekleşir; False (varsayılan) ise dry-run raporu döner.
        """
        # Varsayılan davranış dry-run: yanlışlıkla veri silmeyi önle
        if not execute:
            return await self.dry_run(market, instrument_type, timeframe, symbol)

        policy = await self._fetch_policy(market, instrument_type, timeframe)
        retention_days = policy["retention_days"] if policy else _DEFAULT_RETENTION_DAYS
        cutoff = self._compute_cutoff(retention_days)
        audit_id = str(uuid.uuid4())

        logger.info(
            "[%s] Retention başlıyor: %s %s %s | cutoff=%s",
            audit_id, market, instrument_type, timeframe, cutoff.isoformat(),
        )

        deleted = await self._delete_rows(
            market=market,
            symbol=symbol,
            instrument_type=instrument_type,
            timeframe=timeframe,
            cutoff=cutoff,
            audit_id=audit_id,
        )

        return {
            "dry_run": False,
            "audit_id": audit_id,
            "market": market,
            "instrument_type": instrument_type,
            "timeframe": timeframe,
            "symbol": symbol,
            "retention_days": retention_days,
            "cutoff": cutoff.isoformat(),
            "rows_deleted": deleted,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

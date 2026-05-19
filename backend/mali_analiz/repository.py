"""MySQL depolama katmanı — finansal tablolar, oranlar, log ve uyarılar."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import pymysql
import pymysql.cursors

from backend.mali_analiz.directive_engine import Alert
from backend.mali_analiz.models import FinancialAnalysisResponse

_log = logging.getLogger(__name__)


class FinancialStatementRepository:
    def __init__(self) -> None:
        self.host     = os.environ.get("MYSQL_HOST",     "localhost")
        self.port     = int(os.environ.get("MYSQL_PORT", "3306"))
        self.user     = os.environ.get("MYSQL_USER",     "piyasapilot")
        self.password = os.environ.get("MYSQL_PASSWORD", "")
        self.database = (
            os.environ.get("MYSQL_DATABASE")
            or os.environ.get("MYSQL_DB", "piyasapilot")
        )

    def _connect(self) -> pymysql.Connection:
        return pymysql.connect(
            host=self.host, port=self.port, user=self.user,
            password=self.password, database=self.database,
            charset="utf8mb4", autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )

    # ── Ham satır upsert ──────────────────────────────────────────
    def upsert_raw_rows(self, records: list[dict]) -> None:
        """Her (symbol, period, period_type, statement_type) grubu için DELETE+INSERT.

        ON DUPLICATE KEY UPDATE yerine gruplu silme+ekleme yaparız çünkü borsapy
        her çekimde satırları farklı sırayla döndürebilir ve row_index değişirse
        yeni satırlar birikerek veri şişmesine yol açar.
        """
        if not records:
            return
        # Grupla: (symbol, period, period_type, statement_type) → satır listesi
        from collections import defaultdict
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for rec in records:
            key = (rec["symbol"], rec["period"], rec["period_type"], rec["statement_type"])
            groups[key].append(rec)

        sql_del = """
        DELETE FROM financial_raw_rows
        WHERE symbol=%s AND period=%s AND period_type=%s AND statement_type=%s
        """
        sql_ins = """
        INSERT INTO financial_raw_rows
            (symbol, period, period_type, statement_type, row_index, label, value, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for (sym, period, ptype, stype), recs in groups.items():
                        cur.execute(sql_del, (sym, period, ptype, stype))
                        cur.executemany(sql_ins, [
                            (r["symbol"], r["period"], r["period_type"],
                             r["statement_type"], r["row_index"],
                             r["label"], r["value"], r["source"])
                            for r in recs
                        ])
        except Exception as exc:
            _log.error("upsert_raw_rows failed: %s", exc)

    # ── Hesaplanmış oran upsert ───────────────────────────────────
    def upsert_computed_ratios(self, records: list[dict]) -> None:
        if not records:
            return
        sql = """
        INSERT INTO financial_computed_ratios
            (symbol, period, ratio_key, ratio_name, value, unit, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            ratio_name = VALUES(ratio_name),
            value = VALUES(value),
            unit = VALUES(unit),
            category = VALUES(category),
            updated_at = NOW()
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for rec in records:
                        cur.execute(sql, (
                            rec["symbol"], rec["period"], rec["ratio_key"],
                            rec["ratio_name"], rec["value"],
                            rec.get("unit", "x"), rec.get("category", "diger"),
                        ))
        except Exception as exc:
            _log.error("upsert_computed_ratios failed: %s", exc)

    # ── Fetch log ─────────────────────────────────────────────────
    def log_fetch(
        self,
        symbol: str,
        fetch_type: str,
        *,
        status: str = "ok",
        last_period: str | None = None,
        periods_fetched: int = 0,
        error_message: str | None = None,
    ) -> None:
        sql = """
        INSERT INTO financial_fetch_log
            (symbol, fetch_type, last_period, status, periods_fetched, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        symbol, fetch_type, last_period,
                        status, periods_fetched, error_message,
                    ))
        except Exception as exc:
            _log.error("log_fetch failed: %s", exc)

    def get_last_fetch(self, symbol: str, fetch_type: str) -> dict | None:
        sql = """
        SELECT * FROM financial_fetch_log
        WHERE symbol = %s AND fetch_type = %s
        ORDER BY fetched_at DESC LIMIT 1
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (symbol, fetch_type))
                    return cur.fetchone()
        except Exception:
            return None

    def get_all_fetch_status(self) -> list[dict]:
        """Tüm semboller için son çekim durumunu döner.

        Önce financial_fetch_log'a bakar; log yoksa financial_raw_rows'dan
        gerçek dönem bilgisini alır — eski veri bütünlüğü için.
        """
        # MySQL FULL OUTER JOIN = LEFT JOIN + RIGHT JOIN UNION
        sql = """
        SELECT
            COALESCE(l.symbol, r.symbol) AS symbol,
            COALESCE(l.last_period, r.max_period)     AS last_period,
            COALESCE(l.fetched_at, r.max_fetched)     AS fetched_at,
            COALESCE(l.status, 'ok')                  AS status,
            COALESCE(l.periods_fetched, r.period_cnt) AS periods_fetched
        FROM (
            SELECT l1.symbol, l1.last_period, l1.fetched_at, l1.status, l1.periods_fetched
            FROM financial_fetch_log l1
            INNER JOIN (
                SELECT symbol, MAX(fetched_at) AS max_at
                FROM financial_fetch_log
                WHERE fetch_type = 'quarterly'
                GROUP BY symbol
            ) l2 ON l1.symbol = l2.symbol AND l1.fetched_at = l2.max_at
        ) l
        LEFT JOIN (
            SELECT symbol,
                   MAX(period)            AS max_period,
                   MAX(fetched_at)        AS max_fetched,
                   COUNT(DISTINCT period) AS period_cnt
            FROM financial_raw_rows
            WHERE period_type = 'quarterly'
            GROUP BY symbol
        ) r ON l.symbol = r.symbol
        UNION
        SELECT
            r2.symbol,
            r2.max_period  AS last_period,
            r2.max_fetched AS fetched_at,
            'ok'           AS status,
            r2.period_cnt  AS periods_fetched
        FROM (
            SELECT symbol,
                   MAX(period)            AS max_period,
                   MAX(fetched_at)        AS max_fetched,
                   COUNT(DISTINCT period) AS period_cnt
            FROM financial_raw_rows
            WHERE period_type = 'quarterly'
            GROUP BY symbol
        ) r2
        WHERE r2.symbol NOT IN (
            SELECT DISTINCT symbol FROM financial_fetch_log WHERE fetch_type = 'quarterly'
        )
        ORDER BY symbol
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    return cur.fetchall() or []
        except Exception:
            return []

    # ── Uyarı / direktif ─────────────────────────────────────────
    def insert_alerts(self, symbol: str, alerts: list[Alert]) -> None:
        if not alerts:
            return
        sql = """
        INSERT INTO financial_alerts
            (symbol, alert_type, title, body, severity, period, metric_key, metric_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for a in alerts:
                        cur.execute(sql, (
                            symbol, a.alert_type, a.title, a.body,
                            a.severity, a.period, a.metric_key, a.metric_value,
                        ))
        except Exception as exc:
            _log.error("insert_alerts failed: %s", exc)

    def get_alerts(
        self,
        symbol: str | None = None,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[dict]:
        conditions = []
        params: list[Any] = []
        if symbol:
            conditions.append("symbol = %s")
            params.append(symbol)
        if unread_only:
            conditions.append("is_read = FALSE")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
        SELECT * FROM financial_alerts {where}
        ORDER BY created_at DESC LIMIT %s
        """
        params.append(limit)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall() or []
        except Exception:
            return []

    def mark_alerts_read(self, alert_ids: list[int]) -> None:
        if not alert_ids:
            return
        placeholders = ",".join(["%s"] * len(alert_ids))
        sql = f"UPDATE financial_alerts SET is_read = TRUE WHERE id IN ({placeholders})"
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, alert_ids)
        except Exception as exc:
            _log.error("mark_alerts_read failed: %s", exc)

    # ── Ham veri okuma ────────────────────────────────────────────
    def get_raw_rows(
        self,
        symbol: str,
        statement_type: str,
        period_type: str = "quarterly",
        periods: list[str] | None = None,
    ) -> list[dict]:
        """Belirli sembol+tablo+dönem için ham satırları döner."""
        conditions = ["symbol = %s", "statement_type = %s", "period_type = %s"]
        params: list[Any] = [symbol, statement_type, period_type]
        if periods:
            placeholders = ",".join(["%s"] * len(periods))
            conditions.append(f"period IN ({placeholders})")
            params.extend(periods)
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
        SELECT period, row_index, label, value
        FROM financial_raw_rows {where}
        ORDER BY period DESC, row_index ASC
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall() or []
        except Exception as exc:
            _log.error("get_raw_rows failed: %s", exc)
            return []

    def get_available_periods(self, symbol: str, period_type: str = "quarterly") -> list[str]:
        """Sembol için mevcut dönemleri döner (en yeni önce)."""
        sql = """
        SELECT DISTINCT period FROM financial_raw_rows
        WHERE symbol = %s AND period_type = %s
        ORDER BY period DESC
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (symbol, period_type))
                    rows = cur.fetchall() or []
                    return [r["period"] for r in rows]
        except Exception:
            return []

    def get_computed_ratios(
        self,
        symbol: str,
        periods: list[str] | None = None,
        ratio_keys: list[str] | None = None,
    ) -> list[dict]:
        """Hesaplanmış oranları döner."""
        conditions = ["symbol = %s"]
        params: list[Any] = [symbol]
        if periods:
            placeholders = ",".join(["%s"] * len(periods))
            conditions.append(f"period IN ({placeholders})")
            params.extend(periods)
        if ratio_keys:
            placeholders = ",".join(["%s"] * len(ratio_keys))
            conditions.append(f"ratio_key IN ({placeholders})")
            params.extend(ratio_keys)
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
        SELECT * FROM financial_computed_ratios {where}
        ORDER BY period DESC, category, ratio_key
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall() or []
        except Exception as exc:
            _log.error("get_computed_ratios failed: %s", exc)
            return []

    def get_latest_ratios_all_symbols(
        self,
        symbols: list[str],
        ratio_keys: list[str],
    ) -> list[dict]:
        """Tüm semboller için en güncel dönemin belirtilen oranlarını döner.

        Dönüş: [{symbol, period, ratio_key, ratio_name, value, unit, category}, ...]
        """
        if not symbols or not ratio_keys:
            return []
        sym_placeholders  = ",".join(["%s"] * len(symbols))
        key_placeholders  = ",".join(["%s"] * len(ratio_keys))
        sql = f"""
        SELECT cr.*
        FROM financial_computed_ratios cr
        INNER JOIN (
            SELECT symbol, MAX(period) AS max_period
            FROM financial_computed_ratios
            WHERE symbol IN ({sym_placeholders})
            GROUP BY symbol
        ) latest ON cr.symbol = latest.symbol AND cr.period = latest.max_period
        WHERE cr.ratio_key IN ({key_placeholders})
        ORDER BY cr.symbol, cr.ratio_key
        """
        params: list[Any] = symbols + ratio_keys
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall() or []
        except Exception as exc:
            _log.error("get_latest_ratios_all_symbols failed: %s", exc)
            return []

    def get_market_caps(self, symbols: list[str]) -> dict[str, float | None]:
        """financial_fetch_log'dan piyasa değeri bilgisi çeker (varsa)."""
        if not symbols:
            return {}
        placeholders = ",".join(["%s"] * len(symbols))
        sql = f"""
        SELECT cr.symbol, cr.value AS market_cap
        FROM financial_computed_ratios cr
        INNER JOIN (
            SELECT symbol, MAX(period) AS max_period
            FROM financial_computed_ratios
            WHERE symbol IN ({placeholders})
            GROUP BY symbol
        ) latest ON cr.symbol = latest.symbol AND cr.period = latest.max_period
        WHERE cr.ratio_key = 'market_cap'
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, symbols)
                    rows = cur.fetchall() or []
                    return {r["symbol"]: float(r["market_cap"]) if r["market_cap"] is not None else None for r in rows}
        except Exception:
            return {}

    # ── Eski uyumluluk (v1 service.py hâlâ çağırıyor) ────────────
    def save_response(self, response: FinancialAnalysisResponse, source: str) -> None:
        """V1 uyumluluk metodu — yeni sistemde kullanılmıyor."""
        pass

    # ── Migration helper ──────────────────────────────────────────
    def ensure_tables(self) -> None:
        """Migration dosyasını okuyup tabloları oluşturur (dev/startup için)."""
        import pathlib
        migration = (
            pathlib.Path(__file__).parent.parent.parent
            / "infra" / "mysql" / "migrations" / "006_financial_enhanced.sql"
        )
        if not migration.exists():
            return
        sql_text = migration.read_text(encoding="utf-8")
        statements = [s.strip() for s in sql_text.split(";") if s.strip() and not s.strip().startswith("--")]
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for stmt in statements:
                        if stmt:
                            cur.execute(stmt)
        except Exception as exc:
            _log.warning("ensure_tables: %s", exc)

"""BIST 30 toplu finansal veri çekici.

Uygulama başlatıldığında ve manuel tetiklendiğinde çalışır.
Tüm BIST 30 sembollerini sırayla çeker, MySQL'e yazar, oran hesaplar.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

from backend.mali_analiz.borsapy_provider import FinancialSnapshot, df_to_records, fetch_symbol
from backend.mali_analiz.directive_engine import generate_directives
from backend.mali_analiz.ratio_engine import compute_ratios, ratios_to_db_records
from backend.mali_analiz.symbols import BIST_30_SYMBOLS

_log = logging.getLogger(__name__)


def harvest_all(
    symbols: list[str] | None = None,
    repository: "Any | None" = None,
    max_workers: int = 3,
    inter_batch_delay: float = 2.0,
    on_progress: Callable[[str, str], None] | None = None,
) -> dict[str, str]:
    """Tüm BIST 30 (veya verilen liste) için veri çeker.

    on_progress(symbol, status) → ilerleme callback'i
    Döndürür: {symbol: "ok" | "error: <msg>"}
    """
    targets = symbols or BIST_30_SYMBOLS
    results: dict[str, str] = {}
    _log.info("Harvest başlıyor: %d sembol", len(targets))

    # Toplu çekimde rate limit aşmamak için düşük concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_harvest_one, sym, repository): sym
            for sym in targets
        }
        for future in as_completed(futures):
            sym = futures[future]
            try:
                status = future.result()
                results[sym] = status
                if on_progress:
                    on_progress(sym, status)
                _log.info("Harvest %s: %s", sym, status)
            except Exception as exc:
                results[sym] = f"error: {exc}"
                _log.error("Harvest exception %s: %s", sym, exc)

    _log.info("Harvest tamamlandı: %d/%d başarılı", sum(1 for v in results.values() if v == "ok"), len(targets))
    return results


def _harvest_one(symbol: str, repository: "Any | None") -> str:
    """Tek sembol için fetch → store → ratio döngüsü."""
    try:
        snap = fetch_symbol(symbol, quarterly_periods=40, annual_periods=10)
    except Exception as exc:
        _log.error("fetch_symbol failed for %s: %s", symbol, exc)
        if repository:
            repository.log_fetch(symbol, "quarterly", status="error", error_message=str(exc))
        return f"error: {exc}"

    if snap.error:
        if repository:
            repository.log_fetch(symbol, "quarterly", status="error", error_message=snap.error)
        return f"error: {snap.error}"

    if repository:
        _store_snapshot(snap, repository)

    return "ok"


def _store_snapshot(snap: FinancialSnapshot, repo: "Any") -> None:
    # Ham satırları kaydet
    for stmt_type, df in snap.raw_quarterly.items():
        records = df_to_records(df, snap.symbol, stmt_type, "quarterly")
        repo.upsert_raw_rows(records)

    for stmt_type, df in snap.raw_annual.items():
        records = df_to_records(df, snap.symbol, stmt_type, "annual")
        repo.upsert_raw_rows(records)

    # Oranları hesapla ve kaydet
    period_ratios = compute_ratios(snap)
    ratio_records = ratios_to_db_records(snap.symbol, period_ratios)
    repo.upsert_computed_ratios(ratio_records)

    # Direktifleri/uyarıları üret
    alerts = generate_directives(snap, period_ratios)
    if alerts:
        repo.insert_alerts(snap.symbol, alerts)

    # Fetch log
    last_period = snap.periods_quarterly[0] if snap.periods_quarterly else None
    repo.log_fetch(
        snap.symbol,
        "quarterly",
        status="ok",
        last_period=last_period,
        periods_fetched=len(snap.periods_quarterly),
    )


def needs_refresh(symbol: str, repository: "Any") -> bool:
    """Son çekimden bu yana yeni çeyrek gelmiş olabilir mi?"""
    log = repository.get_last_fetch(symbol, "quarterly")
    if log is None:
        return True
    fetched_at: datetime = log.get("fetched_at")
    if fetched_at is None:
        return True
    # 6 saatten eskiyse kontrol et
    age_hours = (datetime.now(timezone.utc) - fetched_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    return age_hours > 6


def harvest_if_stale(
    repository: "Any",
    max_workers: int = 3,
) -> dict[str, str]:
    """Sadece bayatlamış sembolleri günceller."""
    stale = [s for s in BIST_30_SYMBOLS if needs_refresh(s, repository)]
    if not stale:
        _log.info("Tüm semboller güncel, çekim atlandı.")
        return {}
    _log.info("%d bayatlamış sembol güncelleniyor: %s", len(stale), stale)
    return harvest_all(symbols=stale, repository=repository, max_workers=max_workers)

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


def recompute_ratios_from_stored(symbol: str, repository: "Any") -> str:
    """MySQL'deki ham veri kullanarak oranları yeniden hesaplar.

    borsapy'ye gitmeden sadece stored raw_rows'dan FinancialSnapshot oluşturur.
    market_cap varsa computed_ratios'tan alır, yoksa değerleme oranları None kalır.
    """
    from backend.mali_analiz.borsapy_provider import (
        FinancialSnapshot, _extract, _BS, _IS, _CF, _BS_LABELS, _IS_LABELS, _CF_LABELS
    )
    import pandas as pd

    try:
        # Dönemleri bul
        periods = repository.get_available_periods(symbol, "quarterly")
        if not periods:
            return "no_data"

        def _build_df(stmt_type: str) -> pd.DataFrame:
            rows = repository.get_raw_rows(symbol, stmt_type, "quarterly", periods)
            if not rows:
                return pd.DataFrame()
            # {row_index: {period: value, label: ...}}
            by_label: dict[str, dict[str, float | None]] = {}
            by_ridx:  dict[int, str] = {}
            for r in rows:
                label = r.get("label") or str(r.get("row_index", "?"))
                ridx  = r.get("row_index", 0)
                by_ridx[ridx] = label
                if label not in by_label:
                    by_label[label] = {}
                per = r.get("period", "")
                val = r.get("value")
                if val is not None:
                    try:
                        by_label[label][per] = float(val)
                    except (TypeError, ValueError):
                        by_label[label][per] = None
                else:
                    by_label[label][per] = None

            # Satırları orijinal row_index sırasına göre sırala
            ordered_labels = [by_ridx[k] for k in sorted(by_ridx.keys()) if by_ridx[k] in by_label]
            df = pd.DataFrame(
                [by_label[lbl] for lbl in ordered_labels],
                index=ordered_labels,
                columns=periods,
            )
            df.index = df.index.str.strip()
            return df

        bs_df  = _build_df("balance_sheet")
        inc_df = _build_df("income_stmt")
        cf_df  = _build_df("cashflow")

        # Piyasa değerini eski ratios'tan al (varsa)
        old_fk_rows = repository.get_computed_ratios(symbol, periods=periods[:1], ratio_keys=["pd_dd"])
        pd_dd_val = float(old_fk_rows[0]["value"]) if old_fk_rows and old_fk_rows[0].get("value") is not None else None
        equity_rows = repository.get_raw_rows(symbol, "balance_sheet", "quarterly", periods[:1])
        market_cap = None

        snap = FinancialSnapshot(
            symbol=symbol,
            fetched_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            current_price=None,
            market_cap=market_cap,
            shares_outstanding=None,
            balance_sheet=_extract(bs_df,  _BS,  _BS_LABELS)  if not bs_df.empty  else {},
            income_stmt  =_extract(inc_df, _IS,  _IS_LABELS)  if not inc_df.empty else {},
            cashflow     =_extract(cf_df,  _CF,  _CF_LABELS)  if not cf_df.empty  else {},
            raw_quarterly={"balance_sheet": bs_df, "income_stmt": inc_df, "cashflow": cf_df},
            raw_annual   ={},
            periods_quarterly=periods,
            periods_annual   =[],
        )

        period_ratios = compute_ratios(snap)
        ratio_records = ratios_to_db_records(symbol, period_ratios)
        repository.upsert_computed_ratios(ratio_records)

        alerts = generate_directives(snap, period_ratios)
        if alerts:
            repository.insert_alerts(symbol, alerts)

        repository.log_fetch(
            symbol, "quarterly", status="ok",
            last_period=periods[0],
            periods_fetched=len(periods),
        )
        _log.info("Stored-data ratio recompute OK: %s (%d dönem)", symbol, len(periods))
        return "ok"

    except Exception as exc:
        _log.error("recompute_ratios_from_stored failed for %s: %s", symbol, exc)
        return f"error: {exc}"


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

"""Borsapy tabanlı gerçek finansal veri sağlayıcı.

Borsapy → isyatirim.com üzerinden BIST şirketlerinin
bilanço, gelir tablosu ve nakit akışı verilerini çeker.
Hayali veri üretmez; veri yoksa boş döner.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

_log = logging.getLogger(__name__)

# Label anahtar kelimeleri — borsapy DataFrame index'i alfabetik sırada gelir.
# Her key için sıralı aday etiket parçaları (küçük harf, Türkçe).
_BS_LABELS: dict[str, list[str]] = {
    "current_assets":        ["dönen varlıklar"],
    "cash":                  ["nakit ve nakit benzerleri"],
    "short_fin_investments": ["finansal yatırımlar", "kısa vadeli finansal"],
    "non_current_assets":    ["duran varlıklar"],
    "long_fin_investments":  ["uzun vadeli finansal yatırım"],
    "total_assets":          ["toplam varlıklar", "varlıklar toplamı"],
    "current_liabilities":   ["kısa vadeli yükümlülükler", "kısa vadeli borçlar"],
    "st_financial_debt":     ["kısa vadeli finansal borçlar", "kısa vadeli banka"],
    "long_term_liabilities": ["uzun vadeli yükümlülükler", "uzun vadeli borçlar"],
    "lt_financial_debt":     ["uzun vadeli finansal borçlar", "uzun vadeli banka"],
    "total_equity":          ["özkaynaklar toplamı", "toplam özkaynaklar", "özkaynaklar"],
    "parent_equity":         ["ana ortaklığa ait özkaynaklar"],
    "paid_in_capital":       ["ödenmiş sermaye"],
    "retained_earnings":     ["geçmiş yıllar kâr", "geçmiş yıllar kar"],
    "period_net_income":     ["dönem net kâr", "dönem net kar"],
    "minority_interest":     ["azınlık payları", "kontrol gücü olmayan"],
}

_IS_LABELS: dict[str, list[str]] = {
    # Keyword'ler MySQL'de LOWER(label) olarak saklanmış değerlerle eşleşmeli
    "revenue":               ["satış gelirleri"],
    "cogs":                  ["satışların maliyeti"],
    "gross_profit":          ["brüt kar (zarar)", "ticari faaliyetlerden brüt"],
    "operating_profit":      ["faaliyet kari (zarari)", "faaliyet karı (zarari)", "net faaliyet kar/zarar"],
    "ebit_before_finance":   ["finansman gideri öncesi faaliyet"],
    "financial_income":      ["(esas faaliyet dışı) finansal gelir", "finansal gelirler"],
    "financial_expenses":    ["(esas faaliyet dışı) finansal gider", "finansal giderler (-)"],
    "pretax_income":         ["sürdürülen faaliyetler vergi öncesi kari", "vergi öncesi kari (zarari)"],
    "net_income":            ["dönem kari (zarari)", "dönem karı (zarari)", "sürdürülen faaliyetler dönem kari"],
    "parent_net_income":     ["ana ortaklık payları"],
    "eps":                   ["hisse başına kazanç"],
}

_CF_LABELS: dict[str, list[str]] = {
    "depreciation":    ["amortisman giderleri"],
    "operating_cf":    ["işletme faaliyetlerinden kaynaklanan", "işletme faaliyetleri"],
    "da_total":        ["amortisman ve itfa", "amortisman & itfa"],
    "capex":           ["sabit sermaye yatırımları", "maddi duran varlık alımı"],
    "investing_cf":    ["yatırım faaliyetlerinden kaynaklanan"],
    "fcf":             ["serbest nakit akım", "serbest nakit"],
    "financing_cf":    ["finansman faaliyetlerden kaynaklanan"],
    "end_cash":        ["dönem sonu nakit"],
}

# Pozisyon tabanlı yedek — label bulunamazsa kullanılır
_BS = {
    "current_assets": 0, "cash": 1, "short_fin_investments": 2,
    "non_current_assets": 12, "long_fin_investments": 17,
    "total_assets": 28, "current_liabilities": 30, "st_financial_debt": 31,
    "long_term_liabilities": 44, "lt_financial_debt": 45,
    "total_equity": 57, "parent_equity": 58, "paid_in_capital": 59,
    "retained_earnings": 65, "period_net_income": 66, "minority_interest": 68,
}
_IS = {
    "revenue": 1, "cogs": 2, "gross_profit": 10, "operating_profit": 17,
    "ebit_before_finance": 23, "financial_income": 24, "financial_expenses": 25,
    "pretax_income": 27, "net_income": 35, "parent_net_income": 38, "eps": 39,
}
_CF = {
    "depreciation": 0, "operating_cf": 8, "da_total": 11, "capex": 18,
    "investing_cf": 20, "fcf": 21, "financing_cf": 26, "end_cash": 33,
}


@dataclass
class FinancialSnapshot:
    """Tek sembol için tam finansal veri paketi."""
    symbol: str
    fetched_at: datetime
    current_price: float | None
    market_cap: float | None
    shares_outstanding: float | None
    currency: str = "TRY"
    # Her biri: {period_str: value}, örn. {"2025Q4": 1234567}
    balance_sheet: dict[str, dict[str, float | None]] = field(default_factory=dict)
    income_stmt: dict[str, dict[str, float | None]] = field(default_factory=dict)
    cashflow: dict[str, dict[str, float | None]] = field(default_factory=dict)
    # Ham DataFrame satırları: {stmt_type: {row_idx: {period: value}}}
    raw_quarterly: dict[str, pd.DataFrame] = field(default_factory=dict)
    raw_annual: dict[str, pd.DataFrame] = field(default_factory=dict)
    periods_quarterly: list[str] = field(default_factory=list)
    periods_annual: list[str] = field(default_factory=list)
    error: str | None = None


def _safe(val: Any) -> float | None:
    """NaN/inf/None → None, geçerliyse float."""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f or abs(f) > 1e30:  # NaN veya aşırı büyük
            return None
        return f
    except (TypeError, ValueError):
        return None


def _extract(
    df: pd.DataFrame,
    mapping: dict[str, int],
    label_mapping: dict[str, list[str]] | None = None,
) -> dict[str, dict[str, float | None]]:
    """Label-based extraction, pozisyon tabanlı fallback ile.

    borsapy DataFrame index'i alfabetik sıralı Türkçe etiketler içerir.
    Önce label_mapping'deki anahtar kelimeleri arar (büyük/küçük harf fark etmez),
    bulamazsa mapping'deki pozisyona döner.
    """
    result: dict[str, dict[str, float | None]] = {}
    n_rows = len(df)
    if df.empty:
        return {key: {} for key in mapping}

    # İndeks etiketlerini küçük harfe normalize et → hızlı arama
    index_labels_lower = [str(idx).lower().strip() for idx in df.index]

    def _find_row(keywords: list[str]) -> pd.Series | None:
        for kw in keywords:
            kw_l = kw.lower()
            for i, label in enumerate(index_labels_lower):
                if kw_l in label:
                    return df.iloc[i]
        return None

    for key, pos in mapping.items():
        row = None

        # 1) Label-based arama
        if label_mapping and key in label_mapping:
            row = _find_row(label_mapping[key])

        # 2) Pozisyon tabanlı fallback
        if row is None and pos < n_rows:
            row = df.iloc[pos]

        result[key] = (
            {period: _safe(val) for period, val in row.items()}
            if row is not None else {}
        )
    return result


def fetch_symbol(
    symbol: str,
    quarterly_periods: int = 40,
    annual_periods: int = 10,
    retry: int = 2,
    delay: float = 1.0,
) -> FinancialSnapshot:
    """Tek sembol için borsapy'den veri çeker.

    quarterly_periods=40 → ~10 yıl çeyreklik veri
    annual_periods=10    → 10 yıl yıllık veri
    retry → hata durumunda tekrar sayısı
    delay → istekler arası bekleme (saniye)
    """
    for attempt in range(retry + 1):
        try:
            return _do_fetch(symbol, quarterly_periods, annual_periods, delay)
        except Exception as exc:
            _log.warning("Fetch attempt %d/%d failed for %s: %s", attempt + 1, retry + 1, symbol, exc)
            if attempt < retry:
                time.sleep(delay * (attempt + 1))

    return FinancialSnapshot(
        symbol=symbol,
        fetched_at=datetime.now(timezone.utc),
        current_price=None,
        market_cap=None,
        shares_outstanding=None,
        error="Tüm yeniden deneme girişimleri başarısız.",
    )


def _do_fetch(symbol: str, quarterly_periods: int, annual_periods: int, delay: float) -> FinancialSnapshot:
    import borsapy  # defer — borsapy ağır import

    t = borsapy.Ticker(symbol)

    # Anlık fiyat ve piyasa değeri
    info: dict[str, Any] = {}
    try:
        info = t.info or {}
    except Exception:
        pass
    current_price = _safe(info.get("currentPrice"))
    market_cap = _safe(info.get("marketCap"))
    shares_outstanding = _safe(info.get("sharesOutstanding"))

    time.sleep(delay)

    # Çeyreklik veriler
    try:
        bs_q = t.get_balance_sheet(quarterly=True, last_n=quarterly_periods)
    except Exception as exc:
        _log.warning("%s quarterly balance sheet: %s", symbol, exc)
        bs_q = pd.DataFrame()

    time.sleep(delay * 0.5)

    try:
        inc_q = t.get_income_stmt(quarterly=True, last_n=quarterly_periods)
    except Exception as exc:
        _log.warning("%s quarterly income stmt: %s", symbol, exc)
        inc_q = pd.DataFrame()

    time.sleep(delay * 0.5)

    try:
        cf_q = t.get_cashflow(quarterly=True, last_n=quarterly_periods)
    except Exception as exc:
        _log.warning("%s quarterly cashflow: %s", symbol, exc)
        cf_q = pd.DataFrame()

    time.sleep(delay)

    # Yıllık veriler
    try:
        bs_a = t.get_balance_sheet(quarterly=False, last_n=annual_periods)
    except Exception as exc:
        _log.warning("%s annual balance sheet: %s", symbol, exc)
        bs_a = pd.DataFrame()

    time.sleep(delay * 0.5)

    try:
        inc_a = t.get_income_stmt(quarterly=False, last_n=annual_periods)
    except Exception as exc:
        _log.warning("%s annual income stmt: %s", symbol, exc)
        inc_a = pd.DataFrame()

    time.sleep(delay * 0.5)

    try:
        cf_a = t.get_cashflow(quarterly=False, last_n=annual_periods)
    except Exception as exc:
        _log.warning("%s annual cashflow: %s", symbol, exc)
        cf_a = pd.DataFrame()

    # Normalize index (leading whitespace)
    for df in [bs_q, inc_q, cf_q, bs_a, inc_a, cf_a]:
        if not df.empty:
            df.index = df.index.str.strip()

    periods_q = list(bs_q.columns) if not bs_q.empty else []
    periods_a = list(bs_a.columns) if not bs_a.empty else []

    return FinancialSnapshot(
        symbol=symbol,
        fetched_at=datetime.now(timezone.utc),
        current_price=current_price,
        market_cap=market_cap,
        shares_outstanding=shares_outstanding,
        balance_sheet=_extract(bs_q, _BS, _BS_LABELS) if not bs_q.empty else {},
        income_stmt=_extract(inc_q, _IS, _IS_LABELS) if not inc_q.empty else {},
        cashflow=_extract(cf_q, _CF, _CF_LABELS) if not cf_q.empty else {},
        raw_quarterly={"balance_sheet": bs_q, "income_stmt": inc_q, "cashflow": cf_q},
        raw_annual={"balance_sheet": bs_a, "income_stmt": inc_a, "cashflow": cf_a},
        periods_quarterly=periods_q,
        periods_annual=periods_a,
    )


def df_to_records(df: pd.DataFrame, symbol: str, statement_type: str, period_type: str) -> list[dict]:
    """DataFrame → MySQL'e yazılacak satır listesi."""
    records = []
    if df.empty:
        return records
    for row_idx, (label, row) in enumerate(df.iterrows()):
        for period, value in row.items():
            records.append({
                "symbol": symbol,
                "period": period,
                "period_type": period_type,
                "statement_type": statement_type,
                "row_index": row_idx,
                "label": str(label)[:255],
                "value": _safe(value),
                "source": "borsapy",
            })
    return records

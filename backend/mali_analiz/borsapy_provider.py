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

# DataFrame satır konumları — TFRS formatı (tüm BIST şirketleri aynı yapı)
_BS = {
    "current_assets":          0,   # Dönen Varlıklar
    "cash":                    1,   # Nakit ve Nakit Benzerleri
    "short_fin_investments":   2,   # Finansal Yatırımlar (kısa vadeli)
    "non_current_assets":     12,   # Duran Varlıklar
    "long_fin_investments":   17,   # Finansal Yatırımlar (uzun vadeli)
    "total_assets":           28,   # TOPLAM VARLIKLAR
    "current_liabilities":    30,   # Kısa Vadeli Yükümlülükler
    "st_financial_debt":      31,   # Finansal Borçlar (kısa vadeli)
    "long_term_liabilities":  44,   # Uzun Vadeli Yükümlülükler
    "lt_financial_debt":      45,   # Finansal Borçlar (uzun vadeli)
    "total_equity":           57,   # Özkaynaklar
    "parent_equity":          58,   # Ana Ortaklığa Ait Özkaynaklar
    "paid_in_capital":        59,   # Ödenmiş Sermaye
    "retained_earnings":      65,   # Geçmiş Yıllar Kar/Zararları
    "period_net_income":      66,   # Dönem Net Kar/Zararı
    "minority_interest":      68,   # Azınlık Payları
}

_IS = {
    "revenue":                 1,   # Satış Gelirleri
    "cogs":                    2,   # Satışların Maliyeti (-)
    "gross_profit":           10,   # BRÜT KAR (ZARAR)
    "operating_profit":       17,   # FAALİYET KARI (ZARARI)
    "ebit_before_finance":    23,   # Finansman Gideri Öncesi Faaliyet Karı/Zararı
    "financial_income":       24,   # (Esas Faaliyet Dışı) Finansal Gelirler
    "financial_expenses":     25,   # (Esas Faaliyet Dışı) Finansal Giderler (-)
    "pretax_income":          27,   # SÜRDÜRÜLEN FAALİYETLER VERGİ ÖNCESİ KARI
    "net_income":             35,   # DÖNEM KARI (ZARARI)
    "parent_net_income":      38,   # Ana Ortaklık Payları
    "eps":                    39,   # Hisse Başına Kazanç
}

_CF = {
    "depreciation":            0,   # Amortisman Giderleri
    "operating_cf":            8,   # İşletme Faaliyetlerinden Kaynaklanan Net Nakit
    "da_total":               11,   # Amortisman & İtfa Payları
    "capex":                  18,   # Sabit Sermaye Yatırımları (negatif)
    "investing_cf":           20,   # Yatırım Faaliyetlerinden Kaynaklanan Nakit
    "fcf":                    21,   # Serbest Nakit Akım
    "financing_cf":           26,   # Finansman Faaliyetlerden Kaynaklanan Nakit
    "end_cash":               33,   # Dönem Sonu Nakit
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


def _extract(df: pd.DataFrame, mapping: dict[str, int]) -> dict[str, dict[str, float | None]]:
    """İlgili satır pozisyonlarından {key: {period: value}} çıkarır."""
    result: dict[str, dict[str, float | None]] = {}
    n_rows = len(df)
    for key, pos in mapping.items():
        if pos >= n_rows:
            result[key] = {}
            continue
        row = df.iloc[pos]
        result[key] = {period: _safe(val) for period, val in row.items()}
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
        balance_sheet=_extract(bs_q, _BS) if not bs_q.empty else {},
        income_stmt=_extract(inc_q, _IS) if not inc_q.empty else {},
        cashflow=_extract(cf_q, _CF) if not cf_q.empty else {},
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

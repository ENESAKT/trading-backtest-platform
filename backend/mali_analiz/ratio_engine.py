"""Fastweb / Yaşar Erdinç tarzı finansal oran motoru.

Girdi: FinancialSnapshot (borsapy_provider'dan)
Çıktı: {period: {ratio_key: value}} yapısında hesaplanmış oranlar

Oranlar:
  Değerleme : fk, pd_dd, ev_ebitda, ev_satislar
  Karlılık  : brut_kar_marji, ebitda_marji, net_kar_marji, roe, roa
  Büyüme    : ciro_buyume, net_kar_buyume, ebitda_buyume, ozkaynak_buyume
  Borç      : net_borc, net_borc_ebitda, borc_ozkaynak, faiz_karsilama
  Nakit     : fcf, fcf_marji, fcf_net_kar_orani
  Likidite  : cari_oran, asit_test_oran
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.mali_analiz.borsapy_provider import FinancialSnapshot

_log = logging.getLogger(__name__)

# Oranların Türkçe metadata'sı
RATIO_META: dict[str, dict[str, str]] = {
    # Değerleme
    "fk":              {"name": "F/K Oranı",               "unit": "x",    "category": "deger"},
    "pd_dd":           {"name": "PD/DD Oranı",              "unit": "x",    "category": "deger"},
    "ev_ebitda":       {"name": "EV/EBITDA",                "unit": "x",    "category": "deger"},
    "ev_satislar":     {"name": "EV/Satışlar",              "unit": "x",    "category": "deger"},
    # Karlılık
    "brut_kar_marji":  {"name": "Brüt Kar Marjı",           "unit": "%",    "category": "karlilik"},
    "ebitda_marji":    {"name": "EBITDA Marjı",             "unit": "%",    "category": "karlilik"},
    "net_kar_marji":   {"name": "Net Kar Marjı",            "unit": "%",    "category": "karlilik"},
    "roe":             {"name": "Özkaynak Karlılığı (ROE)", "unit": "%",    "category": "karlilik"},
    "roa":             {"name": "Aktif Karlılık (ROA)",     "unit": "%",    "category": "karlilik"},
    # Büyüme
    "ciro_buyume":     {"name": "Ciro Büyümesi (YoY)",      "unit": "%",    "category": "buyume"},
    "net_kar_buyume":  {"name": "Net Kar Büyümesi (YoY)",   "unit": "%",    "category": "buyume"},
    "ebitda_buyume":   {"name": "EBITDA Büyümesi (YoY)",    "unit": "%",    "category": "buyume"},
    "ozkaynak_buyume": {"name": "Özkaynak Büyümesi (YoY)", "unit": "%",    "category": "buyume"},
    # Borç
    "net_borc":        {"name": "Net Borç (TL)",            "unit": "TRY",  "category": "borc"},
    "net_borc_ebitda": {"name": "Net Borç / EBITDA",        "unit": "x",    "category": "borc"},
    "borc_ozkaynak":   {"name": "Borç / Özkaynak",         "unit": "x",    "category": "borc"},
    "faiz_karsilama":  {"name": "Faiz Karşılama Oranı",    "unit": "x",    "category": "borc"},
    # Nakit
    "fcf":             {"name": "Serbest Nakit Akışı (TL)", "unit": "TRY",  "category": "nakit"},
    "fcf_marji":       {"name": "FCF Marjı",                "unit": "%",    "category": "nakit"},
    "fcf_net_kar":     {"name": "FCF / Net Kar",            "unit": "x",    "category": "nakit"},
    # Likidite
    "cari_oran":       {"name": "Cari Oran",                "unit": "x",    "category": "likidite"},
    "asit_test":       {"name": "Asit-Test Oranı",          "unit": "x",    "category": "likidite"},
    # EBITDA (ara hesap — gösterim için)
    "ebitda":          {"name": "EBITDA (TL)",              "unit": "TRY",  "category": "karlilik"},
}


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _pct_change(new: float | None, old: float | None) -> float | None:
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old) * 100


def _round2(v: float | None) -> float | None:
    return round(v, 2) if v is not None else None


@dataclass
class PeriodRatios:
    period: str
    ratios: dict[str, float | None] = field(default_factory=dict)

    def to_list(self) -> list[dict]:
        result = []
        for key, value in self.ratios.items():
            meta = RATIO_META.get(key, {"name": key, "unit": "x", "category": "diger"})
            result.append({
                "key":      key,
                "name":     meta["name"],
                "value":    _round2(value),
                "unit":     meta["unit"],
                "category": meta["category"],
                "period":   self.period,
            })
        return result


def _get(d: dict[str, dict[str, Any]], key: str, period: str) -> float | None:
    """Belirli key ve dönem için değer döner."""
    inner = d.get(key, {})
    v = inner.get(period)
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f != f or abs(f) > 1e30) else f
    except (TypeError, ValueError):
        return None


def _ttm(d: dict[str, dict[str, Any]], key: str, periods: list[str]) -> float | None:
    """Son 4 çeyreği topla (TTM — Trailing Twelve Months)."""
    if len(periods) < 1:
        return None
    total = 0.0
    count = 0
    for p in periods[:4]:
        v = _get(d, key, p)
        if v is not None:
            total += v
            count += 1
    return total if count > 0 else None


def compute_ratios(snap: FinancialSnapshot) -> list[PeriodRatios]:
    """FinancialSnapshot → her çeyrek için PeriodRatios listesi."""
    results: list[PeriodRatios] = []
    periods = snap.periods_quarterly
    if not periods:
        return results

    bs = snap.balance_sheet
    inc = snap.income_stmt
    cf = snap.cashflow

    # Değerleme için TTM hesap
    ttm_net_income = _ttm(inc, "net_income", periods)
    ttm_revenue    = _ttm(inc, "revenue", periods)
    ttm_op_profit  = _ttm(inc, "operating_profit", periods)
    ttm_da         = _ttm(cf, "da_total", periods)
    ttm_ebitda     = (
        (ttm_op_profit or 0) + abs(ttm_da or 0)
        if ttm_op_profit is not None else None
    )
    ttm_fin_exp    = _ttm(inc, "financial_expenses", periods)
    ttm_fcf        = _ttm(cf, "fcf", periods)

    market_cap = snap.market_cap
    # Enterprise Value = Piyasa Değeri + Net Borç (son dönem)
    latest = periods[0]
    st_debt = _get(bs, "st_financial_debt", latest) or 0
    lt_debt = _get(bs, "lt_financial_debt", latest) or 0
    cash    = (_get(bs, "cash", latest) or 0) + (_get(bs, "short_fin_investments", latest) or 0)
    net_debt_latest = st_debt + lt_debt - cash
    ev = (market_cap or 0) + net_debt_latest if market_cap is not None else None

    for i, period in enumerate(periods):
        r: dict[str, float | None] = {}

        revenue    = _get(inc, "revenue", period)
        gross_p    = _get(inc, "gross_profit", period)
        op_profit  = _get(inc, "operating_profit", period)
        net_income = _get(inc, "net_income", period)
        fin_exp    = _get(inc, "financial_expenses", period)
        da         = _get(cf, "da_total", period)
        op_cf      = _get(cf, "operating_cf", period)
        fcf_val    = _get(cf, "fcf", period)
        capex      = _get(cf, "capex", period)

        total_assets     = _get(bs, "total_assets", period)
        equity           = _get(bs, "total_equity", period)
        current_assets   = _get(bs, "current_assets", period)
        current_liab     = _get(bs, "current_liabilities", period)
        st_debt_p        = _get(bs, "st_financial_debt", period) or 0
        lt_debt_p        = _get(bs, "lt_financial_debt", period) or 0
        cash_p           = (_get(bs, "cash", period) or 0) + (_get(bs, "short_fin_investments", period) or 0)

        # EBITDA
        ebitda = None
        if op_profit is not None and da is not None:
            ebitda = op_profit + abs(da)
        elif op_profit is not None:
            ebitda = op_profit

        # Net Borç
        total_fin_debt = st_debt_p + lt_debt_p
        net_debt = total_fin_debt - cash_p

        # --- DEĞERLEME (sadece son dönem = TTM için anlamlı) ---
        if i == 0:  # en güncel dönem
            r["fk"]          = _round2(_safe_div(market_cap, ttm_net_income))
            r["pd_dd"]       = _round2(_safe_div(market_cap, equity))
            r["ev_ebitda"]   = _round2(_safe_div(ev, ttm_ebitda)) if ttm_ebitda else None
            r["ev_satislar"] = _round2(_safe_div(ev, ttm_revenue)) if ttm_revenue else None

        # --- KARLILIK ---
        r["brut_kar_marji"] = _round2(_safe_div(gross_p,   revenue) * 100 if gross_p and revenue else None)
        r["ebitda_marji"]   = _round2(_safe_div(ebitda,    revenue) * 100 if ebitda and revenue else None)
        r["net_kar_marji"]  = _round2(_safe_div(net_income, revenue) * 100 if net_income and revenue else None)
        r["roe"]            = _round2(_safe_div(net_income, equity)  * 100 if net_income and equity else None)
        r["roa"]            = _round2(_safe_div(net_income, total_assets) * 100 if net_income and total_assets else None)
        r["ebitda"]         = _round2(ebitda)

        # --- BÜYÜME (YoY — 4 çeyrek öncesi ile karşılaştır) ---
        yoy_period = periods[i + 4] if i + 4 < len(periods) else None
        if yoy_period:
            r["ciro_buyume"]     = _round2(_pct_change(revenue,    _get(inc, "revenue",    yoy_period)))
            r["net_kar_buyume"]  = _round2(_pct_change(net_income, _get(inc, "net_income", yoy_period)))
            r["ozkaynak_buyume"] = _round2(_pct_change(equity,     _get(bs,  "total_equity", yoy_period)))
            yoy_ebitda = None
            yoy_op  = _get(inc, "operating_profit", yoy_period)
            yoy_da  = _get(cf,  "da_total", yoy_period)
            if yoy_op is not None and yoy_da is not None:
                yoy_ebitda = yoy_op + abs(yoy_da)
            r["ebitda_buyume"]   = _round2(_pct_change(ebitda, yoy_ebitda))

        # --- BORÇ ---
        r["net_borc"]        = _round2(net_debt)
        r["net_borc_ebitda"] = _round2(_safe_div(net_debt, ebitda * 4) if ebitda else None)  # yıllıklaştırılmış
        r["borc_ozkaynak"]   = _round2(_safe_div(total_fin_debt, equity))
        r["faiz_karsilama"]  = _round2(
            _safe_div(op_profit, abs(fin_exp)) if op_profit and fin_exp else None
        )

        # --- NAKİT ---
        r["fcf"]          = _round2(fcf_val)
        r["fcf_marji"]    = _round2(_safe_div(fcf_val, revenue) * 100 if fcf_val and revenue else None)
        r["fcf_net_kar"]  = _round2(_safe_div(fcf_val, net_income) if fcf_val and net_income else None)

        # --- LİKİDİTE ---
        r["cari_oran"]  = _round2(_safe_div(current_assets, current_liab))
        r["asit_test"]  = None  # Stok verisi yok (THYAO gibi hizmet sektörü için anlamsız)

        results.append(PeriodRatios(period=period, ratios=r))

    return results


def ratios_to_db_records(symbol: str, period_ratios: list[PeriodRatios]) -> list[dict]:
    """PeriodRatios listesini MySQL'e yazılacak dict listesine çevirir."""
    records = []
    for pr in period_ratios:
        for key, value in pr.ratios.items():
            meta = RATIO_META.get(key, {"name": key, "unit": "x", "category": "diger"})
            records.append({
                "symbol":     symbol,
                "period":     pr.period,
                "ratio_key":  key,
                "ratio_name": meta["name"],
                "value":      value,
                "unit":       meta["unit"],
                "category":   meta["category"],
            })
    return records

"""Mali analiz provider normalizasyon ve oran hesaplama yardımcıları."""

from typing import Any

from backend.mali_analiz.models import FinancialAnalysisResponse, SourceStatus


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "")
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den


def get_latest_value(data_dict: dict[str, list[Any]], keys: list[str]) -> float | None:
    """Belirli anahtarlardaki ilk anlamlı değeri (en son dönemi) döner."""
    for key in keys:
        for k, v in data_dict.items():
            if k.lower() == key.lower() or key.lower() in k.lower():
                if isinstance(v, list) and len(v) > 0:
                    return _safe_float(v[0])
    return None


def calculate_ratios(
    bs: dict[str, list[Any]], inc: dict[str, list[Any]], warnings: list[str]
) -> list[dict[str, Any]]:
    ratios = []

    # İlgili kalemleri çek (sadece son dönem)
    gross_profit = get_latest_value(inc, ["brüt kâr", "brut kar", "gross profit"])
    revenue = get_latest_value(inc, ["hasılat", "satiş gelirleri", "revenue", "sales"])
    op_income = get_latest_value(
        inc, ["esas faaliyet kârı", "operating income", "esas faaliyet karı"]
    )
    net_income = get_latest_value(inc, ["net dönem kârı", "net income", "net kar"])

    current_assets = get_latest_value(bs, ["dönen varlıklar", "current assets"])
    current_liabs = get_latest_value(bs, ["kısa vadeli yükümlülükler", "current liabilities"])
    total_liabs = get_latest_value(bs, ["toplam yükümlülükler", "total liabilities"])
    total_equity = get_latest_value(bs, ["özkaynaklar", "toplam özkaynaklar", "total equity"])
    total_assets = get_latest_value(bs, ["toplam varlıklar", "total assets"])

    def add_ratio(name: str, val: float | None, fmt: str = "num"):
        if val is not None:
            ratios.append({"name": name, "value": val, "format": fmt})
        else:
            warnings.append(f"Oran hesaplanamadı: {name} (eksik veri)")

    # 1. gross_margin
    add_ratio("Brüt Kâr Marjı", _safe_div(gross_profit, revenue), "pct")
    # 2. operating_margin
    add_ratio("Faaliyet Kâr Marjı", _safe_div(op_income, revenue), "pct")
    # 3. net_margin
    add_ratio("Net Kâr Marjı", _safe_div(net_income, revenue), "pct")
    # 4. current_ratio
    add_ratio("Cari Oran", _safe_div(current_assets, current_liabs), "num")
    # 5. debt_to_equity
    add_ratio("Borç/Özkaynak", _safe_div(total_liabs, total_equity), "num")
    # 6. return_on_assets
    add_ratio("Aktif Kârlılığı (ROA)", _safe_div(net_income, total_assets), "pct")
    # 7. return_on_equity
    add_ratio("Özkaynak Kârlılığı (ROE)", _safe_div(net_income, total_equity), "pct")
    # 8. asset_turnover
    add_ratio("Aktif Devir Hızı", _safe_div(revenue, total_assets), "num")

    return ratios


def _normalize_dict_to_lists(
    raw_data: Any, num_periods: int, periods: list[str]
) -> dict[str, list[Any]]:
    """Eğer raw_data {label: value} ise {label: [value]} yapar. Eğer {label: {period: value}} ise pad/truncate eder."""
    res = {}
    if not isinstance(raw_data, dict):
        return res
    for k, v in raw_data.items():
        if isinstance(v, dict):
            # Nested dict, e.g. {"2025-Q4": 1000, "2025-Q3": 900}
            row = []
            for p in periods:
                row.append(v.get(p))
            res[k] = row
        elif isinstance(v, list):
            res[k] = v[:num_periods] + [None] * max(0, num_periods - len(v))
        else:
            res[k] = [v] + [None] * max(0, num_periods - 1)
    return res


def normalize_provider_response(raw_data: dict, default_symbol: str) -> FinancialAnalysisResponse:
    warnings = []

    symbol = raw_data.get("symbol", default_symbol).strip().upper()
    if symbol != default_symbol:
        warnings.append(f"Sembol normalize edildi: {default_symbol} -> {symbol}")
        symbol = default_symbol

    company_name = raw_data.get("company_name") or raw_data.get("name")
    if not company_name:
        warnings.append("Şirket adı yok")

    periods = raw_data.get("periods", [])
    if not isinstance(periods, list):
        periods = [str(periods)]
    if len(periods) < 4:
        warnings.append("Dönem sayısı 4'ten az")

    num_periods = len(periods) if periods else 1
    if not periods:
        periods = ["Güncel"]

    bs_raw = raw_data.get("balance_sheet") or raw_data.get("bilanco") or {}
    inc_raw = raw_data.get("income_statement") or raw_data.get("gelir_tablosu") or {}

    bs = _normalize_dict_to_lists(bs_raw, num_periods, periods)
    inc = _normalize_dict_to_lists(inc_raw, num_periods, periods)

    if not bs and not inc:
        warnings.append("Provider boş veri döndürdü")

    ratios = calculate_ratios(bs, inc, warnings)

    # Zaten oranlar geldiyse onları da ekle
    existing_ratios = raw_data.get("ratios")
    if isinstance(existing_ratios, dict):
        for k, v in existing_ratios.items():
            ratios.append({"name": k, "value": _safe_float(v), "format": "num"})
    elif isinstance(existing_ratios, list):
        ratios.extend(existing_ratios)

    # Build financial statements array for UI
    financial_statements = []
    if bs:
        rows = [{"label": k, "values": v} for k, v in bs.items()]
        financial_statements.append({"title": "Bilanço", "rows": rows})
    if inc:
        rows = [{"label": k, "values": v} for k, v in inc.items()]
        financial_statements.append({"title": "Gelir Tablosu", "rows": rows})

    status_str = "ok"
    source_str = "normalized"
    raw_status = raw_data.get("source_status")

    if isinstance(raw_status, dict):
        status_str = raw_status.get("status", "ok")
        source_str = raw_status.get("source", "normalized")
    elif isinstance(raw_status, str):
        status_str = raw_status
        source_str = raw_data.get("source", "normalized")
    else:
        source_str = raw_data.get("source", "normalized")

    if not bs and not inc:
        status_str = "empty"
    elif not bs or not inc:
        status_str = "partial"

    source_status = SourceStatus(source=source_str, status=status_str)

    # Gelen existing warnings
    raw_warnings = raw_data.get("warnings", [])
    if isinstance(raw_warnings, list):
        warnings.extend(raw_warnings)

    return FinancialAnalysisResponse(
        symbol=symbol,
        company_name=company_name,
        periods=periods,
        balance_sheet=bs,
        income_statement=inc,
        cash_flow={},
        financial_statements=financial_statements,
        ratios=ratios,
        source_status=source_status,
        warnings=warnings,
    )

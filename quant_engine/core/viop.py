"""VİOP/vadeli ürünlerde kontrat özellikleri ve güvenlik kapıları."""

from __future__ import annotations

import decimal
from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ViopContractAssumption(BaseModel):
    """VİOP kontrat özelliklerini tanımlayan varsayım modeli."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    underlying: str | None = None
    contract_type: Literal["future", "option", "unknown"] = "unknown"
    expiry: date | None = None
    multiplier: float | None = None
    tick_size: float | None = None
    initial_margin: float | None = None
    maintenance_margin: float | None = None
    leverage: float | None = None
    currency: str = "TRY"
    settlement_type: Literal["cash", "physical", "unknown"] = "unknown"
    data_source: str = "not_configured"
    is_real_data: bool = False
    rollover_policy: str | None = None


def check_viop_gate(
    contract: ViopContractAssumption,
    current_date: date | None = None,
) -> dict[str, Any]:
    """
    Paper/backtest işlemlerinde sahte veri veya eksik parametreleri engelleyen güvenlik kapısı.
    """
    allowed = True
    blocking_reasons = []
    warnings = []

    if not contract.is_real_data:
        blocking_reasons.append("Sahte (mock) veri kullanılıyor")
    if contract.data_source == "not_configured":
        blocking_reasons.append("Veri kaynağı tanımlanmamış (not_configured)")
    if contract.tick_size is None or contract.tick_size <= 0:
        blocking_reasons.append("Geçerli tick_size eksik")
    if contract.multiplier is None or contract.multiplier <= 0:
        blocking_reasons.append("Geçerli multiplier eksik")
    if contract.expiry is None:
        blocking_reasons.append("Expiry (vade sonu) bilgisi eksik")
    if contract.initial_margin is None or contract.initial_margin <= 0:
        blocking_reasons.append("Geçerli initial_margin bilgisi eksik")
    if contract.maintenance_margin is None or contract.maintenance_margin <= 0:
        blocking_reasons.append("Geçerli maintenance_margin bilgisi eksik")
    if contract.rollover_policy is None or contract.rollover_policy.lower() == "none":
        blocking_reasons.append("Rollover politikası eksik")

    today = current_date or _utc_now().date()

    if contract.expiry:
        days_to_expiry = (contract.expiry - today).days
        if days_to_expiry < 0:
            blocking_reasons.append(f"Kontrat vadesi geçmiş (expiry={contract.expiry})")
        elif days_to_expiry <= 3:
            warnings.append(f"Vade sonuna çok az kaldı: {days_to_expiry} gün")

    if blocking_reasons:
        allowed = False

    return {
        "allowed": allowed,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "assumptions": contract.model_dump(mode="json"),
    }


def tick_round(price: float, tick_size: float) -> float:
    """Fiyatı tick_size katsayısına göre yuvarlar."""
    if tick_size <= 0:
        raise ValueError("tick_size pozitif olmalıdır")
    if price < 0:
        raise ValueError("price negatif olamaz")

    p_dec = decimal.Decimal(str(price))
    t_dec = decimal.Decimal(str(tick_size))

    # 0.5 mantığıyla (round half up/even) standart yuvarlama
    # Decimal quantize tick_size tabanlı çalışması için:
    scaled = p_dec / t_dec
    rounded_scaled = scaled.quantize(decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP)
    result = rounded_scaled * t_dec
    return float(result)


def calculate_viop_pnl(
    entry_price: float,
    exit_price: float,
    direction: Literal["long", "short"],
    multiplier: float,
    quantity: float = 1.0,
) -> float:
    """
    Multiplier bazlı VİOP PnL hesaplaması.
    """
    if entry_price < 0 or exit_price < 0:
        raise ValueError("Fiyatlar negatif olamaz")
    if multiplier <= 0:
        raise ValueError("Multiplier pozitif olmalıdır")
    if quantity <= 0:
        raise ValueError("Quantity pozitif olmalıdır")

    diff = exit_price - entry_price if direction == "long" else entry_price - exit_price
    return float(diff * multiplier * quantity)

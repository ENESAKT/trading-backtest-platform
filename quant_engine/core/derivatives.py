"""Opsiyon, varant ve swap ürünleri için risk/varsayım kapısı katmanı."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DerivativeAssumption(BaseModel):
    """Türev ürün özelliklerini tanımlayan varsayım modeli."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    instrument_type: Literal["option", "warrant", "swap", "unknown"] = "unknown"
    underlying: str | None = None
    expiry: date | None = None  # Option/warrant for expiry, Swap for maturity
    currency: str = "TRY"
    data_source: str = "not_configured"
    is_real_data: bool = False
    liquidity_status: Literal["high", "medium", "low", "unknown"] = "unknown"
    settlement_type: Literal["cash", "physical", "unknown"] = "unknown"

    # Option / Warrant fields
    option_type: Literal["call", "put", "none"] = "none"
    strike: float | None = None
    multiplier: float | None = None
    premium: float | None = None
    implied_volatility: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None

    # Swap fields
    notional: float | None = None
    fixed_rate: float | None = None
    floating_rate_index: str | None = None
    reset_frequency: str | None = None


def check_derivative_gate(
    contract: DerivativeAssumption,
    current_date: date | None = None,
) -> dict[str, Any]:
    """
    Türev ürünler için risk uyarıları ve işlem yapılabilirliğini denetleyen kapı (gate).
    """
    allowed = True
    blocking_reasons = []
    warnings = []

    # 1. Genel kontroller
    if not contract.is_real_data:
        blocking_reasons.append("Sahte (mock) veri kullanılıyor")
    if contract.data_source == "not_configured":
        blocking_reasons.append("Veri kaynağı tanımlanmamış (not_configured)")
    if contract.expiry is None:
        blocking_reasons.append("Vade (expiry/maturity) bilgisi eksik")

    today = current_date or _utc_now().date()
    if contract.expiry:
        days_to_expiry = (contract.expiry - today).days
        if days_to_expiry < 0:
            blocking_reasons.append(f"Vadesi geçmiş (expiry={contract.expiry})")
        elif days_to_expiry <= 3:
            warnings.append(f"Vade sonuna çok az kaldı: {days_to_expiry} gün")

    if contract.liquidity_status in ("low", "unknown"):
        warnings.append(f"Likidite durumu düşük veya bilinmiyor: {contract.liquidity_status}")

    warnings.append("Gerçek fiyatlama teorik motor içermez, eğitim/simülasyon modudur")

    # 2. Ürün tipine özel kontroller
    if contract.instrument_type in ("option", "warrant"):
        if contract.strike is None or contract.strike <= 0:
            blocking_reasons.append("Geçerli strike (kullanım fiyatı) eksik")
        if contract.option_type == "none":
            blocking_reasons.append("Geçerli option_type (call/put) eksik")
        if contract.multiplier is None or contract.multiplier <= 0:
            blocking_reasons.append("Geçerli multiplier eksik")
        if contract.premium is None or contract.premium < 0:
            blocking_reasons.append("Geçerli premium bilgisi eksik")

        # Opsiyon/varant risk uyarıları
        if contract.implied_volatility is None:
            warnings.append("Implied volatility (IV) eksik")
        if any(g is None for g in (contract.delta, contract.gamma, contract.theta, contract.vega)):
            warnings.append("Greeks (Delta, Gamma, Theta, Vega) verilerinde eksiklik var")
        if contract.multiplier and contract.premium and contract.multiplier > 100:
            warnings.append(f"Yüksek çarpan riski: {contract.multiplier}")

    elif contract.instrument_type == "swap":
        if contract.notional is None or contract.notional <= 0:
            blocking_reasons.append("Geçerli notional (anapara) eksik")
        if contract.fixed_rate is None or contract.floating_rate_index is None:
            blocking_reasons.append("Geçerli fixed_rate veya floating_rate_index eksik")
        warnings.append("Swap faiz ve reset riski (piyasa faiz hareketleri simüle edilmeyebilir)")

    else:
        blocking_reasons.append("Tanımsız veya desteklenmeyen türev ürün tipi (instrument_type)")

    if blocking_reasons:
        allowed = False

    return {
        "allowed": allowed,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "assumptions": contract.model_dump(mode="json"),
    }


def calculate_option_pnl(
    underlying_price: float,
    strike: float,
    premium_paid: float,
    multiplier: float,
    option_type: Literal["call", "put"],
    direction: Literal["long", "short"],
    quantity: float = 1.0,
) -> dict[str, Any]:
    """
    Opsiyon/Varant için prim (premium) bazlı basit simülasyon/eğitim PnL hesaplaması.
    Not: Erken kullanım veya zaman değeri primini değil, sadece vade sonu içsel değeri + ödenen/alınan primi dikkate alan basit hesaplamadır.
    """
    if any(v < 0 for v in (underlying_price, strike, premium_paid)):
        raise ValueError("Fiyat, strike veya prim negatif olamaz")
    if multiplier <= 0 or quantity <= 0:
        raise ValueError("Multiplier ve quantity pozitif olmalıdır")

    # Vade sonundaki (veya teorik) içsel değer (Intrinsic Value)
    intrinsic_value = 0.0
    if option_type == "call":
        intrinsic_value = max(0.0, underlying_price - strike)
    elif option_type == "put":
        intrinsic_value = max(0.0, strike - underlying_price)
    else:
        raise ValueError("Geçersiz option_type")

    # Toplam değer
    gross_pnl = 0.0
    if direction == "long":
        # Alıcı: İçsel değerden ödediği primi çıkar
        gross_pnl = (intrinsic_value - premium_paid) * multiplier * quantity
    elif direction == "short":
        # Satıcı: Aldığı primden içsel değeri (zararı) çıkar
        gross_pnl = (premium_paid - intrinsic_value) * multiplier * quantity
    else:
        raise ValueError("Geçersiz direction")

    return {
        "label": "eğitim/simülasyon",
        "pnl": float(gross_pnl),
        "intrinsic_value": float(intrinsic_value),
    }


def calculate_swap_pnl(
    notional: float,
    fixed_rate: float,
    current_floating_rate: float,
    direction: Literal["pay_fixed", "receive_fixed"],
) -> dict[str, Any]:
    """
    Çok basit bir notional * rate difference hesaplaması.
    Not: Gerçek faiz çarpanı, gün sayımı konvansiyonu ve iskonto eğrisi dahil değildir.
    """
    if notional <= 0:
        raise ValueError("Notional pozitif olmalıdır")

    # Rates are assumed to be in percentages (e.g., 5.0 for 5%)
    rate_diff = 0.0
    if direction == "pay_fixed":
        # Sabit öde, değişken al
        rate_diff = current_floating_rate - fixed_rate
    elif direction == "receive_fixed":
        # Sabit al, değişken öde
        rate_diff = fixed_rate - current_floating_rate
    else:
        raise ValueError("Geçersiz direction")

    # Basit bir yüzde olarak kabul et (örn: 5.0 -> %5)
    pnl = notional * (rate_diff / 100.0)

    return {
        "label": "eğitim/simülasyon",
        "pnl": float(pnl),
    }

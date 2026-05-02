"""Tests for Derivatives gate and helpers."""

from datetime import date, timedelta

import pytest

from quant_engine.core.derivatives import (
    DerivativeAssumption,
    calculate_option_pnl,
    calculate_swap_pnl,
    check_derivative_gate,
)


def _valid_option() -> DerivativeAssumption:
    return DerivativeAssumption(
        symbol="O_XU030E1225C10000",
        instrument_type="option",
        underlying="XU030",
        expiry=date.today() + timedelta(days=10),
        currency="TRY",
        data_source="bist_viop",
        is_real_data=True,
        liquidity_status="high",
        settlement_type="cash",
        option_type="call",
        strike=10000.0,
        multiplier=10.0,
        premium=150.0,
        implied_volatility=0.25,
        delta=0.5,
        gamma=0.01,
        theta=-1.5,
        vega=10.2,
    )


def _valid_swap() -> DerivativeAssumption:
    return DerivativeAssumption(
        symbol="SWAP_TRY_3M",
        instrument_type="swap",
        underlying="TRY_RATE",
        expiry=date.today() + timedelta(days=90),
        currency="TRY",
        data_source="bloomberg",
        is_real_data=True,
        liquidity_status="high",
        settlement_type="cash",
        notional=1000000.0,
        fixed_rate=35.0,
        floating_rate_index="TRLIBOR_3M",
        reset_frequency="3M",
    )


def test_derivative_gate_allowed_option():
    opt = _valid_option()
    result = check_derivative_gate(opt, current_date=date.today())

    assert result["allowed"] is True
    assert result["blocking_reasons"] == []
    # Contains the educational/simulation warning
    assert any("eğitim/simülasyon" in w for w in result["warnings"])


def test_derivative_gate_allowed_swap():
    swp = _valid_swap()
    result = check_derivative_gate(swp, current_date=date.today())

    assert result["allowed"] is True
    assert result["blocking_reasons"] == []
    assert any("Swap faiz" in w for w in result["warnings"])


def test_derivative_gate_not_real_data():
    opt = _valid_option()
    opt.is_real_data = False
    result = check_derivative_gate(opt, current_date=date.today())

    assert result["allowed"] is False
    assert "Sahte (mock) veri kullanılıyor" in result["blocking_reasons"]


def test_derivative_gate_past_expiry():
    opt = _valid_option()
    today = date.today()
    opt.expiry = today - timedelta(days=5)
    result = check_derivative_gate(opt, current_date=today)

    assert result["allowed"] is False
    assert any("Vadesi geçmiş" in r for r in result["blocking_reasons"])


def test_derivative_gate_missing_option_fields():
    opt = _valid_option()
    opt.strike = None
    opt.premium = -1.0
    result = check_derivative_gate(opt, current_date=date.today())

    assert result["allowed"] is False
    assert any("Geçerli strike" in r for r in result["blocking_reasons"])
    assert any("Geçerli premium bilgisi" in r for r in result["blocking_reasons"])


def test_derivative_gate_low_liquidity():
    opt = _valid_option()
    opt.liquidity_status = "low"
    result = check_derivative_gate(opt, current_date=date.today())

    assert result["allowed"] is True  # Sadece uyarı fırlatır
    assert any("Likidite durumu düşük" in w for w in result["warnings"])


def test_calculate_option_pnl_call():
    # Long Call: Strike=100, Premium=5, Multiplier=10. Underlying=120
    # Intrinsic: 120 - 100 = 20. Net profit: (20 - 5) * 10 = 150
    res1 = calculate_option_pnl(120, 100, 5, 10, "call", "long", 1)
    assert res1["intrinsic_value"] == 20.0
    assert res1["pnl"] == 150.0

    # Short Call: Same scenario. Net profit: (5 - 20) * 10 = -150
    res2 = calculate_option_pnl(120, 100, 5, 10, "call", "short", 1)
    assert res2["pnl"] == -150.0

    # Underlying < Strike -> Intrinsic=0.
    res3 = calculate_option_pnl(90, 100, 5, 10, "call", "long", 1)
    assert res3["intrinsic_value"] == 0.0
    assert res3["pnl"] == -50.0


def test_calculate_option_pnl_put():
    # Long Put: Strike=100, Premium=5, Multiplier=10. Underlying=80
    # Intrinsic: 100 - 80 = 20. Net profit: (20 - 5) * 10 = 150
    res1 = calculate_option_pnl(80, 100, 5, 10, "put", "long", 1)
    assert res1["intrinsic_value"] == 20.0
    assert res1["pnl"] == 150.0

    # Underlying > Strike -> Intrinsic=0.
    res2 = calculate_option_pnl(120, 100, 5, 10, "put", "long", 1)
    assert res2["intrinsic_value"] == 0.0
    assert res2["pnl"] == -50.0


def test_calculate_swap_pnl():
    # Pay fixed 35%, receive floating 40%, Notional 1000
    # rate_diff = 40 - 35 = 5. pnl = 1000 * (5 / 100) = 50
    res1 = calculate_swap_pnl(1000.0, 35.0, 40.0, "pay_fixed")
    assert res1["pnl"] == 50.0

    # Receive fixed 35%, pay floating 40%
    # rate_diff = 35 - 40 = -5. pnl = 1000 * (-5 / 100) = -50
    res2 = calculate_swap_pnl(1000.0, 35.0, 40.0, "receive_fixed")
    assert res2["pnl"] == -50.0

def test_invalid_parameters():
    with pytest.raises(ValueError, match="Geçersiz direction"):
        calculate_option_pnl(100, 100, 5, 10, "call", "invalid")

    with pytest.raises(ValueError, match="Geçersiz option_type"):
        calculate_option_pnl(100, 100, 5, 10, "invalid", "long")

    with pytest.raises(ValueError, match="Geçersiz direction"):
        calculate_swap_pnl(1000.0, 35.0, 40.0, "invalid")

"""Tests for VIOP contract gate and helpers."""

from datetime import date, timedelta

import pytest

from quant_engine.core.viop import (
    ViopContractAssumption,
    calculate_viop_pnl,
    check_viop_gate,
    tick_round,
)


def _valid_contract() -> ViopContractAssumption:
    return ViopContractAssumption(
        symbol="F_XU0301225",
        underlying="XU030",
        contract_type="future",
        expiry=date.today() + timedelta(days=10),
        multiplier=10.0,
        tick_size=0.25,
        initial_margin=15000.0,
        maintenance_margin=15000.0,
        leverage=10.0,
        currency="TRY",
        settlement_type="cash",
        data_source="bist_viop",
        is_real_data=True,
        rollover_policy="auto_roll",
    )


def test_viop_gate_allowed():
    contract = _valid_contract()
    result = check_viop_gate(contract, current_date=date.today())

    assert result["allowed"] is True
    assert result["blocking_reasons"] == []
    assert result["warnings"] == []
    assert result["assumptions"]["symbol"] == "F_XU0301225"


def test_viop_gate_not_real_data_is_blocking():
    contract = _valid_contract()
    contract.is_real_data = False
    result = check_viop_gate(contract, current_date=date.today())

    assert result["allowed"] is False
    assert "Sahte (mock) veri kullanılıyor" in result["blocking_reasons"]


def test_viop_gate_missing_multiplier_is_blocking():
    contract = _valid_contract()
    contract.multiplier = None
    result = check_viop_gate(contract, current_date=date.today())

    assert result["allowed"] is False
    assert "Geçerli multiplier eksik" in result["blocking_reasons"]


def test_viop_gate_missing_rollover_is_blocking():
    contract = _valid_contract()
    contract.rollover_policy = "none"
    result = check_viop_gate(contract, current_date=date.today())

    assert result["allowed"] is False
    assert "Rollover politikası eksik" in result["blocking_reasons"]


def test_viop_gate_past_expiry_is_blocking():
    contract = _valid_contract()
    today = date.today()
    contract.expiry = today - timedelta(days=1)
    result = check_viop_gate(contract, current_date=today)

    assert result["allowed"] is False
    assert any("vadesi geçmiş" in reason for reason in result["blocking_reasons"])


def test_viop_gate_close_expiry_warning():
    contract = _valid_contract()
    today = date.today()
    contract.expiry = today + timedelta(days=2)
    result = check_viop_gate(contract, current_date=today)

    assert result["allowed"] is True
    assert result["blocking_reasons"] == []
    assert any("az kaldı" in warning for warning in result["warnings"])


def test_tick_round_normal_behavior():
    assert tick_round(100.12, 0.25) == 100.00
    assert tick_round(100.13, 0.25) == 100.25
    assert tick_round(100.37, 0.25) == 100.25
    assert tick_round(100.38, 0.25) == 100.50
    assert tick_round(10.04, 0.05) == 10.05
    assert tick_round(10.02, 0.05) == 10.00


def test_tick_round_invalid_inputs():
    with pytest.raises(ValueError, match="pozitif olmalıdır"):
        tick_round(100.0, 0.0)
    with pytest.raises(ValueError, match="negatif olamaz"):
        tick_round(-100.0, 0.25)


def test_calculate_viop_pnl_long():
    # Long: 100.0'den girip 110.0'dan çıkmak, multiplier 10, quantity 2
    pnl = calculate_viop_pnl(100.0, 110.0, "long", multiplier=10.0, quantity=2.0)
    assert pnl == 200.0


def test_calculate_viop_pnl_short():
    # Short: 110.0'den girip 100.0'dan çıkmak, multiplier 10, quantity 1
    pnl = calculate_viop_pnl(110.0, 100.0, "short", multiplier=10.0, quantity=1.0)
    assert pnl == 100.0


def test_calculate_viop_pnl_invalid_inputs():
    with pytest.raises(ValueError, match="negatif olamaz"):
        calculate_viop_pnl(-10.0, 100.0, "long", 10.0)
    with pytest.raises(ValueError, match="pozitif olmalıdır"):
        calculate_viop_pnl(10.0, 100.0, "long", 0.0)

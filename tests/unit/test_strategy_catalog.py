import pytest

from quant_engine.strategy.catalog import (
    CATEGORIES,
    get_strategy_preset,
    list_strategy_presets,
    preset_to_strategy_spec,
)
from quant_engine.strategy.spec import RULE_NAMES, validate_strategy_spec


REQUIRED_METADATA_FIELDS = {
    "id",
    "label",
    "category",
    "expected_market",
    "suggested_timeframes",
    "min_bars",
    "suggested_stop_pct",
    "suggested_take_profit_pct",
    "repaint_risk",
    "liquidity_need",
    "description",
}


def test_strategy_catalog_lists_at_least_ten_presets_with_complete_metadata():
    presets = list_strategy_presets()

    assert len(presets) >= 10
    assert {preset["category"] for preset in presets} == set(CATEGORIES)

    ids = [preset["id"] for preset in presets]
    assert len(ids) == len(set(ids))

    for preset in presets:
        assert REQUIRED_METADATA_FIELDS <= set(preset)
        assert preset["id"]
        assert preset["label"]
        assert preset["category"] in CATEGORIES
        assert preset["expected_market"]
        assert preset["suggested_timeframes"]
        assert preset["min_bars"] > 0
        assert preset["suggested_stop_pct"] > 0
        assert preset["suggested_take_profit_pct"] > 0
        assert preset["repaint_risk"] in {"low", "medium", "high"}
        assert preset["liquidity_need"] in {"low", "medium", "high"}
        assert preset["description"]
        assert "rules" not in preset


def test_strategy_catalog_can_include_strategy_spec_payloads():
    presets = list_strategy_presets(include_spec=True)

    for preset in presets:
        assert "strategy_spec" in preset
        assert preset["strategy_spec"] == preset_to_strategy_spec(preset["id"])


def test_every_preset_produces_valid_non_empty_strategy_spec_dict():
    for preset in list_strategy_presets():
        spec = preset_to_strategy_spec(preset["id"])
        normalized = validate_strategy_spec(spec)

        assert spec["preset_id"] == preset["id"]
        assert spec["category"] == preset["category"]
        assert normalized["name"] == preset["label"]
        assert set(normalized["rules"]) == set(RULE_NAMES)
        assert any(normalized["rules"].values())
        assert normalized["risk"]["stop_loss_pct"] == preset["suggested_stop_pct"]
        assert normalized["risk"]["take_profit_pct"] == preset["suggested_take_profit_pct"]

        for rule in normalized["rules"].values():
            assert "__" not in rule
            assert "IMPORT" not in rule.upper()


def test_get_strategy_preset_returns_metadata_and_spec():
    preset = get_strategy_preset("momentum_rsi_macd")

    assert REQUIRED_METADATA_FIELDS <= set(preset)
    assert preset["strategy_spec"] == preset_to_strategy_spec("momentum_rsi_macd")


def test_unknown_strategy_preset_id_raises_key_error():
    with pytest.raises(KeyError):
        get_strategy_preset("does_not_exist")

    with pytest.raises(KeyError):
        preset_to_strategy_spec("does_not_exist")

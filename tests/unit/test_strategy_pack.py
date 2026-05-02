from __future__ import annotations

import json

import pytest

from quant_engine.strategy.pack import (
    PACK_FILENAME,
    PACK_VERSION,
    export_strategy_pack,
    export_strategy_pack_json,
    import_strategy_pack,
)


def _strategy_spec() -> dict:
    return {
        "name": "EMA RSI Pack",
        "rules": {
            "long_entry": "C > EMA(C,20) AND RSI(C,14) > 50",
            "long_exit": "C < EMA(C,20)",
            "short_entry": "",
            "short_exit": "",
        },
        "risk": {"stop_loss_pct": 2, "take_profit_pct": 5},
    }


def test_exported_pack_is_json_serializable_dict():
    pack = export_strategy_pack(
        _strategy_spec(),
        params={"timeframe": "1d", "symbols": ["THYAO"]},
        indicator_set={"EMA": [20], "RSI": [14]},
        risk_settings={"max_position_pct": 10},
        description="Test paketi",
        example_backtest_metadata={"symbol": "THYAO", "bars": 250},
    )

    encoded = json.dumps(pack, ensure_ascii=False)
    decoded = json.loads(encoded)

    assert PACK_FILENAME == ".piyasapilot-strategy.json"
    assert decoded["version"] == PACK_VERSION
    assert decoded["strategy_spec"]["name"] == "EMA RSI Pack"
    assert decoded["params"]["symbols"] == ["THYAO"]


def test_exported_pack_can_be_returned_as_json_string():
    encoded = export_strategy_pack_json(_strategy_spec(), description="JSON")
    decoded = json.loads(encoded)

    assert decoded["version"] == PACK_VERSION
    assert decoded["description"] == "JSON"
    assert decoded["strategy_spec"]["rules"]["long_entry"].startswith("C > EMA")


def test_import_returns_same_normalized_strategy_spec_from_json():
    exported = export_strategy_pack(
        _strategy_spec(),
        params={"timeframe": "1d"},
        indicator_set=["EMA", "RSI"],
        risk_settings={"stop_loss_pct": 2},
        description="Round trip",
        example_backtest_metadata={"total_return_pct": 12.5},
        as_json=True,
    )

    imported = import_strategy_pack(exported)

    assert imported["strategy_spec"] == export_strategy_pack(_strategy_spec())["strategy_spec"]
    assert imported["params"] == {"timeframe": "1d"}
    assert imported["indicator_set"] == ["EMA", "RSI"]
    assert imported["description"] == "Round trip"


def test_import_rejects_missing_version():
    pack = export_strategy_pack(_strategy_spec())
    del pack["version"]

    with pytest.raises(ValueError, match="version"):
        import_strategy_pack(pack)


def test_import_rejects_missing_strategy_spec():
    pack = export_strategy_pack(_strategy_spec())
    del pack["strategy_spec"]

    with pytest.raises(ValueError, match="strategy_spec"):
        import_strategy_pack(pack)


def test_import_rejects_dangerous_strategy_spec():
    pack = export_strategy_pack(_strategy_spec())
    pack["strategy_spec"] = {"long_entry": "__import__(os)"}

    with pytest.raises(ValueError, match="Geçersiz strategy_spec"):
        import_strategy_pack(pack)


def test_import_rejects_empty_strategy_spec():
    pack = export_strategy_pack(_strategy_spec())
    pack["strategy_spec"] = {"name": "Boş", "rules": {}}

    with pytest.raises(ValueError, match="Geçersiz strategy_spec"):
        import_strategy_pack(pack)


def test_export_rejects_non_json_serializable_fields():
    with pytest.raises(ValueError, match="params"):
        export_strategy_pack(_strategy_spec(), params={"bad": object()})

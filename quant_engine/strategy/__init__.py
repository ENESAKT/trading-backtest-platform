"""Quant Engine — Strategy Module."""

from quant_engine.strategy.catalog import (
    CATEGORIES,
    get_strategy_preset,
    list_strategy_presets,
    preset_to_strategy_spec,
)

__all__ = [
    "CATEGORIES",
    "get_strategy_preset",
    "list_strategy_presets",
    "preset_to_strategy_spec",
]

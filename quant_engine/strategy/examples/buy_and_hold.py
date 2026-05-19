"""
Quant Engine — Buy & Hold Baseline Stratejisi

En basit benchmark: ilk barda al, son bara kadar tut.

Her stratejinin performansı bununla karşılaştırılmalı.
Buy & Hold'u yenemeyen strateji faydasızdır.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.registry import register_strategy


@register_strategy
class BuyAndHold(BaseStrategy):
    """Buy & Hold — İlk barda al, asla satma."""

    name = "buy_and_hold"
    description = "Baseline: İlk barda al, son bara kadar tut"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {}

    @property
    def warm_up_bars(self) -> int:
        return 0

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        """İlk barda al, sonra bekle."""
        position = portfolio.get_or_create_position(
            data.iloc[bar_index].get("symbol", "UNKNOWN")
        )
        if bar_index == 0 and not position.is_open:
            return 1  # AL
        return 0  # BEKLE

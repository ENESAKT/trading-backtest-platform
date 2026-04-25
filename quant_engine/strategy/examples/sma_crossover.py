"""
Quant Engine — SMA Crossover Stratejisi

Klasik çift hareketli ortalama kesişim stratejisi.

Kurallar:
    - fast_sma > slow_sma → AL (golden cross)
    - fast_sma < slow_sma → SAT (death cross)
    - Warm-up: slow_period bar

Varsayılan parametreler:
    - fast_period: 10
    - slow_period: 30
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import sma
from quant_engine.strategy.registry import register_strategy


@register_strategy
class SmaCrossover(BaseStrategy):
    """SMA Crossover — Golden/Death Cross stratejisi."""

    name = "sma_crossover"
    description = "Çift SMA kesişim stratejisi (Golden/Death Cross)"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {
            "fast_period": 10,
            "slow_period": 30,
        }

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("slow_period")

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        """
        SMA kesişim sinyali üret.

        Golden Cross (fast > slow): +1 (AL)
        Death Cross (fast < slow): -1 (SAT)
        """
        fast_period = self.get_param("fast_period")
        slow_period = self.get_param("slow_period")

        # Yeterli veri kontrolü
        if bar_index < slow_period:
            return 0

        close = data["close"]
        fast_sma = sma(close, fast_period)
        slow_sma = sma(close, slow_period)

        current_fast = fast_sma.iloc[bar_index]
        current_slow = slow_sma.iloc[bar_index]

        if pd.isna(current_fast) or pd.isna(current_slow):
            return 0

        # Önceki barın değerlerini de kontrol et (kesişim)
        if bar_index >= slow_period + 1:
            prev_fast = fast_sma.iloc[bar_index - 1]
            prev_slow = slow_sma.iloc[bar_index - 1]

            if pd.isna(prev_fast) or pd.isna(prev_slow):
                return 0

            position = portfolio.get_or_create_position(
                data.iloc[bar_index].get("symbol", "UNKNOWN")
            )

            # Golden Cross: fast yukarı kesiyor
            if prev_fast <= prev_slow and current_fast > current_slow:
                if not position.is_open:
                    return 1  # AL

            # Death Cross: fast aşağı kesiyor
            if prev_fast >= prev_slow and current_fast < current_slow:
                if position.is_open:
                    return -1  # SAT

        return 0

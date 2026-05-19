from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import macd
from quant_engine.strategy.registry import register_strategy


@register_strategy
class MacdDivergence(BaseStrategy):
    """MACD sinyal çizgisi kesişim stratejisi."""

    name = "macd_divergence"
    description = "MACD sinyal çizgisi kesişim stratejisi"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("slow_period") + self.get_param("signal_period")

    def validate_params(self) -> list[str]:
        errors = super().validate_params()
        fast = self.get_param("fast_period")
        slow = self.get_param("slow_period")
        if fast >= slow:
            errors.append(f"fast_period ({fast}) < slow_period ({slow}) olmalı")
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        _, _, histogram = macd(
            data["close"],
            fast_period=self.get_param("fast_period"),
            slow_period=self.get_param("slow_period"),
            signal_period=self.get_param("signal_period"),
        )
        self._prepared_data = {"histogram": histogram}

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        if bar_index < self.warm_up_bars + 1:
            return 0

        histogram = self._prepared_data["histogram"]
        curr = histogram.iloc[bar_index]
        prev = histogram.iloc[bar_index - 1]

        if pd.isna(curr) or pd.isna(prev):
            return 0

        symbol = data.iloc[bar_index].get("symbol", "UNKNOWN")
        position = portfolio.get_or_create_position(symbol)

        if prev < 0 and curr >= 0 and not position.is_open:
            return 1
        if prev >= 0 and curr < 0 and position.is_open:
            return -1
        return 0

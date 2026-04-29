from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import atr
from quant_engine.strategy.registry import register_strategy


@register_strategy
class Supertrend(BaseStrategy):
    """ATR tabanlı Supertrend trend takip stratejisi."""

    name = "supertrend"
    description = "ATR tabanlı Supertrend trend takip stratejisi"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {"period": 10, "multiplier": 3.0}

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("period") * 2

    def validate_params(self) -> list[str]:
        errors = super().validate_params()
        if self.get_param("period") < 2:
            errors.append("period >= 2 olmalı")
        if self.get_param("multiplier") <= 0:
            errors.append("multiplier > 0 olmalı")
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        period = self.get_param("period")
        multiplier = float(self.get_param("multiplier"))

        high = data["high"]
        low = data["low"]
        close = data["close"]

        hl2 = (high + low) / 2.0
        atr_vals = atr(high, low, close, period)

        basic_upper = (hl2 + multiplier * atr_vals).values.astype(float)
        basic_lower = (hl2 - multiplier * atr_vals).values.astype(float)
        close_arr = close.values.astype(float)

        n = len(close_arr)
        final_upper = basic_upper.copy()
        final_lower = basic_lower.copy()
        trend = np.zeros(n, dtype=float)

        for i in range(1, n):
            if np.isnan(basic_upper[i]) or np.isnan(basic_lower[i]):
                trend[i] = trend[i - 1]
                final_upper[i] = final_upper[i - 1]
                final_lower[i] = final_lower[i - 1]
                continue

            final_upper[i] = (
                basic_upper[i]
                if basic_upper[i] < final_upper[i - 1] or close_arr[i - 1] > final_upper[i - 1]
                else final_upper[i - 1]
            )
            final_lower[i] = (
                basic_lower[i]
                if basic_lower[i] > final_lower[i - 1] or close_arr[i - 1] < final_lower[i - 1]
                else final_lower[i - 1]
            )

            if trend[i - 1] == -1:
                trend[i] = 1.0 if close_arr[i] > final_upper[i] else -1.0
            else:
                trend[i] = -1.0 if close_arr[i] < final_lower[i] else 1.0

        self._prepared_data = {"trend": pd.Series(trend, index=close.index)}

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        if bar_index < self.warm_up_bars + 1:
            return 0

        trend = self._prepared_data["trend"]
        curr = trend.iloc[bar_index]
        prev = trend.iloc[bar_index - 1]

        symbol = data.iloc[bar_index].get("symbol", "UNKNOWN")
        position = portfolio.get_or_create_position(symbol)

        if curr == 1 and prev == -1 and not position.is_open:
            return 1
        if curr == -1 and prev == 1 and position.is_open:
            return -1
        return 0

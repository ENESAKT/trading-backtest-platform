from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.registry import register_strategy


@register_strategy
class DonchianBreakout(BaseStrategy):
    """Donchian kanalı kırılım stratejisi."""

    name = "donchian_breakout"
    description = "Donchian kanalı kırılım stratejisi"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {"period": 20}

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("period")

    def validate_params(self) -> list[str]:
        errors = super().validate_params()
        period = self.get_param("period")
        if period < 2:
            errors.append(f"period >= 2 olmalı (mevcut: {period})")
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        period = self.get_param("period")
        self._prepared_data = {
            "upper": data["high"].rolling(window=period, min_periods=period).max(),
            "lower": data["low"].rolling(window=period, min_periods=period).min(),
        }

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        if bar_index < self.warm_up_bars + 1:
            return 0

        upper = self._prepared_data["upper"]
        lower = self._prepared_data["lower"]

        prev_upper = upper.iloc[bar_index - 1]
        prev_lower = lower.iloc[bar_index - 1]

        if pd.isna(prev_upper) or pd.isna(prev_lower):
            return 0

        close = float(data["close"].iloc[bar_index])
        symbol = data.iloc[bar_index].get("symbol", "UNKNOWN")
        position = portfolio.get_or_create_position(symbol)

        if close > float(prev_upper) and not position.is_open:
            return 1
        if close < float(prev_lower) and position.is_open:
            return -1
        return 0

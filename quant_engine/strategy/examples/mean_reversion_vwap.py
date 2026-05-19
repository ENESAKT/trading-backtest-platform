from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.registry import register_strategy


@register_strategy
class MeanReversionVwap(BaseStrategy):
    """VWAP ortalama geri dönüş stratejisi."""

    name = "mean_reversion_vwap"
    description = "VWAP ortalama geri dönüş stratejisi"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {"period": 20, "threshold_pct": 1.5}

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("period")

    def validate_params(self) -> list[str]:
        errors = super().validate_params()
        if self.get_param("period") < 2:
            errors.append("period >= 2 olmalı")
        if self.get_param("threshold_pct") <= 0:
            errors.append("threshold_pct > 0 olmalı")
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        period = self.get_param("period")
        typical = (data["high"] + data["low"] + data["close"]) / 3.0
        vol = data["volume"]
        tp_vol = typical * vol
        vwap = (
            tp_vol.rolling(window=period, min_periods=period).sum()
            / vol.rolling(window=period, min_periods=period).sum()
        )
        self._prepared_data = {"vwap": vwap}

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        if bar_index < self.warm_up_bars:
            return 0

        vwap_val = self._prepared_data["vwap"].iloc[bar_index]
        if pd.isna(vwap_val):
            return 0

        close = float(data["close"].iloc[bar_index])
        threshold = float(self.get_param("threshold_pct")) / 100.0
        symbol = data.iloc[bar_index].get("symbol", "UNKNOWN")
        position = portfolio.get_or_create_position(symbol)

        if close < float(vwap_val) * (1.0 - threshold) and not position.is_open:
            return 1
        if close >= float(vwap_val) and position.is_open:
            return -1
        return 0

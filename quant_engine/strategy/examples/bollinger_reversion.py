"""
Quant Engine - Bollinger Band dönüş stratejisi.

Kurallar:
    - Kapanış alt bandın altına iner ve pozisyon yoksa AL
    - Kapanış seçili çıkış bandının üstüne çıkarsa SAT

Bu strateji trend takip etmekten çok mean-reversion mantığıyla çalışır.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import bollinger_bands
from quant_engine.strategy.registry import register_strategy


@register_strategy
class BollingerReversion(BaseStrategy):
    """Bollinger Band - Alt banttan dönüş stratejisi."""

    name = "bollinger_reversion"
    description = "Bollinger alt bandından dönüş, orta/üst bantta çıkış"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {
            "period": 20,
            "num_std": 2.0,
            "exit_band": "middle",
        }

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("period")

    def validate_params(self) -> list[str]:
        """Bollinger parametrelerini doğrula."""
        errors = super().validate_params()
        period = self.get_param("period")
        num_std = self.get_param("num_std")
        exit_band = self.get_param("exit_band")

        if period < 2:
            errors.append(f"period >= 2 olmalı (mevcut: {period})")
        if num_std <= 0:
            errors.append(f"num_std > 0 olmalı (mevcut: {num_std})")
        if exit_band not in {"middle", "upper"}:
            errors.append("exit_band sadece 'middle' veya 'upper' olabilir")
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        """Bollinger bantlarını önceden hesapla."""
        upper, middle, lower = bollinger_bands(
            data["close"],
            period=self.get_param("period"),
            num_std=self.get_param("num_std"),
        )
        self._prepared_data = {
            "upper": upper,
            "middle": middle,
            "lower": lower,
        }

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        """
        Bollinger dönüş sinyali üret.

        Close <= lower band ve pozisyon yoksa AL.
        Close >= middle/upper band ve pozisyon varsa SAT.
        """
        if bar_index < self.warm_up_bars:
            return 0

        if "upper" in self._prepared_data:
            upper = self._prepared_data["upper"]
            middle = self._prepared_data["middle"]
            lower = self._prepared_data["lower"]
        else:
            upper, middle, lower = bollinger_bands(
                data["close"],
                period=self.get_param("period"),
                num_std=self.get_param("num_std"),
            )

        close = float(data["close"].iloc[bar_index])
        lower_value = lower.iloc[bar_index]
        middle_value = middle.iloc[bar_index]
        upper_value = upper.iloc[bar_index]

        if pd.isna(lower_value) or pd.isna(middle_value) or pd.isna(upper_value):
            return 0

        position = portfolio.get_or_create_position(
            data.iloc[bar_index].get("symbol", "UNKNOWN")
        )
        exit_target = (
            upper_value
            if self.get_param("exit_band") == "upper"
            else middle_value
        )

        if close <= lower_value and not position.is_open:
            return 1
        if close >= exit_target and position.is_open:
            return -1
        return 0

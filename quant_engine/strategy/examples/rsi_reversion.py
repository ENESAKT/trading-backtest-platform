"""
Quant Engine — RSI Mean Reversion Stratejisi

RSI aşırı alım/satım bölgelerinden dönüş stratejisi.

Kurallar:
    - RSI < oversold → AL (aşırı satım bölgesinden dönüş)
    - RSI > overbought → SAT (aşırı alım bölgesinden çıkış)

Varsayılan parametreler:
    - rsi_period: 14
    - oversold: 30
    - overbought: 70
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.indicators import rsi
from quant_engine.strategy.registry import register_strategy


@register_strategy
class RsiReversion(BaseStrategy):
    """RSI Mean Reversion — Aşırı alım/satım dönüş."""

    name = "rsi_reversion"
    description = (
        "RSI aşırı alım/satım bölgelerinden "
        "dönüş stratejisi"
    )
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
        }

    @property
    def warm_up_bars(self) -> int:
        return self.get_param("rsi_period") + 1

    def validate_params(self) -> list[str]:
        """RSI parametrelerini doğrula."""
        errors = super().validate_params()
        period = self.get_param("rsi_period")
        oversold = self.get_param("oversold")
        overbought = self.get_param("overbought")

        if period < 2:
            errors.append(
                f"rsi_period >= 2 olmalı "
                f"(mevcut: {period})"
            )
        if oversold >= overbought:
            errors.append(
                f"oversold ({oversold}) < "
                f"overbought ({overbought}) olmalı"
            )
        if not 0 <= oversold <= 100:
            errors.append(
                f"oversold 0-100 arası olmalı "
                f"(mevcut: {oversold})"
            )
        if not 0 <= overbought <= 100:
            errors.append(
                f"overbought 0-100 arası olmalı "
                f"(mevcut: {overbought})"
            )
        return errors

    def prepare(self, data: pd.DataFrame) -> None:
        """RSI'ı önceden hesapla."""
        rsi_period = self.get_param("rsi_period")
        self._prepared_data = {
            "rsi": rsi(data["close"], rsi_period),
        }

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        """
        RSI sinyali üret.

        RSI < oversold ve pozisyon yok → AL
        RSI > overbought ve pozisyon var → SAT
        """
        rsi_period = self.get_param("rsi_period")
        oversold = self.get_param("oversold")
        overbought = self.get_param("overbought")

        if bar_index < rsi_period + 1:
            return 0

        # Cache'den oku veya hesapla
        if "rsi" in self._prepared_data:
            rsi_values = self._prepared_data["rsi"]
        else:
            rsi_values = rsi(
                data["close"], rsi_period
            )

        current_rsi = rsi_values.iloc[bar_index]

        if pd.isna(current_rsi):
            return 0

        position = portfolio.get_or_create_position(
            data.iloc[bar_index].get(
                "symbol", "UNKNOWN"
            )
        )

        # Aşırı satım → AL
        if (
            current_rsi < oversold
            and not position.is_open
        ):
            return 1

        # Aşırı alım → SAT
        if (
            current_rsi > overbought
            and position.is_open
        ):
            return -1

        return 0

"""LightGBM probability stratejisi.

Model dosyası yoksa veya ``lightgbm`` paketi kurulu değilse sahte karar
üretmez; yalnızca HOLD döner. Eğitim çıktısı ``make retrain`` ile üretilir.
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio
from quant_engine.research.lightgbm_model import predict_latest_probability
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.registry import register_strategy


@register_strategy
class LightgbmProbability(BaseStrategy):
    """Eğitilmiş LightGBM modelinin yükseliş olasılığıyla sinyal üretir."""

    name = "lightgbm_probability"
    description = "LightGBM olasılık skoru ile AL/SAT filtresi"
    version = "1.0"

    @property
    def default_params(self) -> dict[str, Any]:
        return {
            "model_path": "",
            "buy_threshold": 0.65,
            "sell_threshold": 0.35,
        }

    @property
    def warm_up_bars(self) -> int:
        return 30

    def validate_params(self) -> list[str]:
        errors = super().validate_params()
        buy_threshold = float(self.get_param("buy_threshold"))
        sell_threshold = float(self.get_param("sell_threshold"))
        if not 0.0 < sell_threshold < buy_threshold < 1.0:
            errors.append("0 < sell_threshold < buy_threshold < 1 olmalı")
        return errors

    @staticmethod
    def _bars_from_frame(data: pd.DataFrame, bar_index: int) -> list[dict[str, Any]]:
        frame = data.iloc[: bar_index + 1]
        return [
            {
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            }
            for _, row in frame.iterrows()
        ]

    def _model_path(self) -> str:
        configured = str(self.get_param("model_path") or "").strip()
        return configured or os.getenv("LIGHTGBM_MODEL_PATH", "")

    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        model_path = self._model_path()
        if not model_path:
            return 0
        probability = predict_latest_probability(
            self._bars_from_frame(data, bar_index),
            model_path,
        )
        if probability is None:
            return 0
        if probability >= float(self.get_param("buy_threshold")):
            return 1
        if probability <= float(self.get_param("sell_threshold")):
            return -1
        return 0

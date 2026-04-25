"""
Quant Engine — BaseStrategy (Soyut Strateji Sınıfı)

Tüm stratejiler bu sınıfı miras alır. Engine ile Strategy arasında
sözleşme kurarak her stratejinin aynı arayüzü sunmasını garanti eder.

Kullanım:
    from quant_engine.strategy.base import BaseStrategy

    class MyStrategy(BaseStrategy):
        name = "my_strategy"
        def generate_signals(self, data, bar_index, portfolio):
            ...
            return signal  # +1, -1, 0

Execution Spec Hatırlatma:
    - bar[t].close'da sinyal üret
    - bar[t+1].open'da execute et
    - Warm-up bitmeden sinyal üretme
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quant_engine.backtest.domain import Portfolio


@dataclass(frozen=True)
class StrategyParams:
    """Strateji parametreleri — immutable, hashable."""
    name: str
    params: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        param_str = ", ".join(
            f"{k}={v}" for k, v in self.params.items()
        )
        return f"{self.name}({param_str})"


class BaseStrategy(ABC):
    """
    Tüm stratejilerin temel sınıfı.

    Alt sınıflar:
    - name: Strateji adı (zorunlu)
    - default_params: Varsayılan parametreler
    - warm_up_bars: Warm-up bar sayısı
    - generate_signals(): Sinyal üretme fonksiyonu
    """

    name: str = "unnamed_strategy"
    description: str = ""
    version: str = "1.0"

    def __init__(self, params: dict[str, Any] | None = None):
        """
        Args:
            params: Strateji parametreleri.
                    None ise default_params kullanılır.
        """
        merged = dict(self.default_params)
        if params:
            # Bilinmeyen parametre kontrolü
            unknown = set(params.keys()) - set(
                self.default_params.keys()
            )
            if unknown:
                raise ValueError(
                    f"Bilinmeyen parametreler: {unknown}. "
                    f"İzin verilenler: "
                    f"{set(self.default_params.keys())}"
                )
            merged.update(params)
        self._params = merged

    @property
    def default_params(self) -> dict[str, Any]:
        """Varsayılan parametreler — alt sınıflar override eder."""
        return {}

    @property
    def warm_up_bars(self) -> int:
        """Warm-up bar sayısı — alt sınıflar override eder."""
        return 0

    @property
    def params(self) -> dict[str, Any]:
        """Aktif parametreler."""
        return dict(self._params)

    def get_param(self, key: str) -> Any:
        """Tek parametre oku."""
        return self._params[key]

    @abstractmethod
    def generate_signals(
        self,
        data: pd.DataFrame,
        bar_index: int,
        portfolio: Portfolio,
    ) -> int:
        """
        Sinyal üret.

        Args:
            data: OHLCV verisi
            bar_index: Mevcut bar indeksi
            portfolio: Portföy durumu

        Returns:
            int: +1 = AL, -1 = SAT, 0 = BEKLE
        """
        ...

    def as_signal_func(self):
        """
        Engine'in beklediği signal_func formatına çevir.

        Warm-up kontrolü dahil.
        """
        def _signal_func(
            data: pd.DataFrame,
            bar_index: int,
            portfolio: Portfolio,
        ) -> int:
            if bar_index < self.warm_up_bars:
                return 0
            return self.generate_signals(
                data, bar_index, portfolio
            )
        return _signal_func

    def get_strategy_params(self) -> StrategyParams:
        """StrategyParams nesnesi döndür."""
        return StrategyParams(
            name=self.name,
            params=self.params,
        )

    def __repr__(self) -> str:
        return str(self.get_strategy_params())

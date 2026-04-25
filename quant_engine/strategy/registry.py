"""
Quant Engine — Strateji Registry

Strateji keşfi ve kayıt sistemi.

Kullanım:
    from quant_engine.strategy.registry import StrategyRegistry

    registry = StrategyRegistry()
    registry.register(SmaCrossover)

    strategy = registry.create("sma_crossover", {"fast": 10, "slow": 30})
    available = registry.list_strategies()
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from quant_engine.strategy.base import BaseStrategy


class StrategyRegistry:
    """
    Strateji kayıt ve keşif sistemi.

    Tüm stratejiler burada kayıt olur, isimle erişilir.
    """

    def __init__(self):
        self._strategies: dict[str, type[BaseStrategy]] = {}

    def register(self, strategy_cls: type[BaseStrategy]) -> None:
        """
        Strateji sınıfını kaydet.

        Args:
            strategy_cls: BaseStrategy alt sınıfı

        Raises:
            TypeError: BaseStrategy alt sınıfı değilse
            ValueError: Aynı isimle kayıtlı strateji varsa
        """
        if not (
            isinstance(strategy_cls, type)
            and issubclass(strategy_cls, BaseStrategy)
        ):
            raise TypeError(
                f"{strategy_cls} BaseStrategy alt sınıfı değil."
            )

        name = strategy_cls.name
        if name in self._strategies:
            raise ValueError(
                f"'{name}' zaten kayıtlı. "
                f"Mevcut: {self._strategies[name]}"
            )

        self._strategies[name] = strategy_cls
        logger.debug(f"📋 Strateji kaydedildi: {name}")

    def create(
        self,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> BaseStrategy:
        """
        İsimle strateji oluştur.

        Args:
            name: Strateji adı
            params: Parametreler (opsiyonel)

        Returns:
            BaseStrategy: Oluşturulmuş strateji

        Raises:
            KeyError: Strateji bulunamazsa
        """
        if name not in self._strategies:
            available = list(self._strategies.keys())
            raise KeyError(
                f"'{name}' bulunamadı. "
                f"Mevcut stratejiler: {available}"
            )

        cls = self._strategies[name]
        return cls(params=params)

    def list_strategies(self) -> list[dict[str, Any]]:
        """Kayıtlı stratejileri listele."""
        result = []
        for name, cls in self._strategies.items():
            instance = cls()
            result.append({
                "name": name,
                "description": cls.description,
                "version": cls.version,
                "default_params": instance.default_params,
                "warm_up_bars": instance.warm_up_bars,
            })
        return result

    def get_names(self) -> list[str]:
        """Kayıtlı strateji isimlerini döndür."""
        return list(self._strategies.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._strategies

    def __len__(self) -> int:
        return len(self._strategies)


# ---------------------------------------------------------------------------
# Global Registry Singleton
# ---------------------------------------------------------------------------

_global_registry = StrategyRegistry()


def get_registry() -> StrategyRegistry:
    """Global strateji registry'sine eriş."""
    return _global_registry


def register_strategy(cls: type[BaseStrategy]) -> type[BaseStrategy]:
    """
    Decorator: Stratejiyi global registry'ye kaydet.

    Kullanım:
        @register_strategy
        class MyStrategy(BaseStrategy):
            name = "my_strategy"
            ...
    """
    _global_registry.register(cls)
    return cls

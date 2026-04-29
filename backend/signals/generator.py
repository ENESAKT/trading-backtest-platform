"""Bar kapanışında strateji koleksiyonunu çalıştırıp sinyal üret.

Her worker (Binance WS / Yahoo poller / BIST poller) ``on_bar`` hook'una
``SignalGenerator.evaluate``'i bağlar. Cache'teki son N barı çek,
``BaseStrategy.generate_signals`` çağır, +1/-1 dönerse ``SignalBus``'a
publish et.

Tasarım kararları:

* **Lookback short**: 200 bar yeter (warm-up + son birkaç değer).
* **Stratejiler asenkron, blocking değil**: ``run_in_executor`` ile
  thread pool'a kaçırılır (pandas/numpy hesabı).
* **Per-strategy state yok**: her bar'da fresh ``prepare``; cache'in
  arttırdığı maliyet düşük çünkü pandas vektör.
* **Idempotent**: aynı barda aynı sinyal tekrar üretilirse yine yayınlar
  (downstream filtresi frontend'de — sembol+strategy+timestamp anahtarı).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.api.signal_bus import SignalBus
from backend.data.cache import OHLCVCache
from quant_engine.backtest.domain import Portfolio
from quant_engine.strategy.registry import StrategyRegistry, get_registry

logger = logging.getLogger(__name__)


@dataclass
class SignalGeneratorConfig:
    lookback_bars: int = 200
    capital: float = 100_000.0
    strategies: list[str] = field(default_factory=list)
    """Boş ise tüm registry kullanılır."""


def _bars_to_dataframe(bars: list[dict[str, Any]], symbol: str) -> pd.DataFrame:
    df = pd.DataFrame(bars)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["symbol"] = symbol
    return df[["date", "symbol", "open", "high", "low", "close", "volume"]]


class SignalGenerator:
    """Cache'ten en güncel pencereyi çek, stratejileri çalıştır, sinyal yayınla."""

    def __init__(
        self,
        cache: OHLCVCache,
        bus: SignalBus,
        config: SignalGeneratorConfig | None = None,
        registry: StrategyRegistry | None = None,
    ):
        self.cache = cache
        self.bus = bus
        self.config = config or SignalGeneratorConfig()
        self._registry = registry or get_registry()
        self.evaluated_count = 0
        self.signal_count = 0
        self.error_count = 0
        self.last_error: str | None = None

    async def evaluate(self, symbol: str, interval: str, bars: list[dict[str, Any]]) -> None:
        """Worker ``on_bar`` hook entry point.

        ``bars`` worker'ın az önce yazdığı son barlardır. Cache'in tamamı
        zaten yazılmış olduğu için biz cache'ten son ``lookback_bars``
        kadarını okuruz.
        """
        del bars  # bilgi amaçlı; cache zaten güncel
        try:
            await self._run_in_executor(symbol, interval)
            self.evaluated_count += 1
        except Exception as exc:  # noqa: BLE001
            self.error_count += 1
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("signal_generator: %s", self.last_error)

    async def _run_in_executor(self, symbol: str, interval: str) -> None:
        loop = asyncio.get_running_loop()
        signals = await loop.run_in_executor(None, self._compute_signals, symbol, interval)
        for sig in signals:
            await self.bus.publish(**sig)
            self.signal_count += 1

    def _strategy_names(self) -> list[str]:
        if self.config.strategies:
            return list(self.config.strategies)
        return self._registry.get_names()

    def _compute_signals(self, symbol: str, interval: str) -> list[dict[str, Any]]:
        canonical = symbol.upper()
        raw_bars = self.cache.get_window(canonical, interval, limit=self.config.lookback_bars)
        if len(raw_bars) < 30:
            return []

        df = _bars_to_dataframe(raw_bars, canonical)
        last_index = len(df) - 1
        last_bar = df.iloc[last_index]
        price = float(last_bar["close"])

        portfolio = Portfolio(initial_capital=self.config.capital)
        emit: list[dict[str, Any]] = []

        for name in self._strategy_names():
            try:
                strategy = self._registry.create(name)
            except KeyError:
                continue
            errors = strategy.validate_params()
            if errors:
                continue
            strategy.prepare(df)
            signal_int = strategy.as_signal_func()(df, last_index, portfolio)
            if signal_int == 0:
                continue
            sig_type = "BUY" if signal_int > 0 else "SELL"
            emit.append(
                {
                    "symbol": canonical,
                    "signal_type": sig_type,
                    "price": price,
                    "strategy_id": name,
                    "reason": f"{name}: {sig_type} @ {price:.2f}",
                    "strength": 5,
                    "interval": interval,
                }
            )
        return emit

    def stats(self) -> dict[str, Any]:
        return {
            "evaluated": self.evaluated_count,
            "signals_emitted": self.signal_count,
            "errors": self.error_count,
            "last_error": self.last_error,
            "strategies": self._strategy_names(),
        }


def utc_iso_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

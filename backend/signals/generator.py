"""Bar kapanışında strateji koleksiyonunu çalıştırıp sinyal üret.

Her worker (Binance WS / Yahoo poller / BIST poller) ``on_bar`` hook'una
``SignalGenerator.evaluate``'i bağlar. Cache'teki son N barı çek,
``BaseStrategy.generate_signals`` çağır, +1/-1 dönerse ``SignalBus``'a
publish et.

Sprint 6.1 — Geliştirilmiş sinyal tipleri:
* **Sinyal gücü (1–10):** Strateji güven seviyesi
* **Konsensüs:** Aynı sembolde 5+ strateji aynı yönde → STRONG
* **Metadata:** RSI, trend yönü, volatilite bilgisi
* **8 Sinyal tipi:** BUY, SELL, STRONG_BUY, STRONG_SELL, HOLD,
  TRAILING_STOP, TAKE_PROFIT, STOP_LOSS

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
from backend.config import getenv
from backend.data.cache import OHLCVCache
from quant_engine.backtest.domain import Portfolio
from quant_engine.research import lightgbm_model
from quant_engine.strategy.persistence import StrategyStore
from quant_engine.strategy.registry import StrategyRegistry, get_registry
from quant_engine.strategy.spec import evaluate_strategy_rules

logger = logging.getLogger(__name__)


@dataclass
class SignalGeneratorConfig:
    lookback_bars: int = 200
    capital: float = 100_000.0
    strategies: list[str] = field(default_factory=list)
    """Boş ise tüm registry kullanılır."""
    consensus_threshold: int = 5
    """Aynı yönde kaç strateji sinyali → STRONG sinyal."""


def _bars_to_dataframe(bars: list[dict[str, Any]], symbol: str) -> pd.DataFrame:
    df = pd.DataFrame(bars)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["symbol"] = symbol
    return df[["date", "symbol", "open", "high", "low", "close", "volume"]]


def _compute_rsi(closes: pd.Series, period: int = 14) -> float:
    """Son RSI değerini hesapla."""
    if len(closes) < period + 1:
        return 50.0
    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window=period, min_periods=period).mean().iloc[-1]
    avg_loss = losses.rolling(window=period, min_periods=period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Son ATR değerini hesapla."""
    if len(df) < period + 1:
        return 0.0
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(window=period, min_periods=period).mean().iloc[-1])


def _trend_direction(closes: pd.Series, fast: int = 20, slow: int = 50) -> str:
    """EMA tabanlı trend yönü."""
    if len(closes) < slow:
        return "NEUTRAL"
    ema_fast = closes.ewm(span=fast, adjust=False).mean().iloc[-1]
    ema_slow = closes.ewm(span=slow, adjust=False).mean().iloc[-1]
    if ema_fast > ema_slow * 1.005:
        return "BULLISH"
    elif ema_fast < ema_slow * 0.995:
        return "BEARISH"
    return "NEUTRAL"


def _compute_strength(signal_int: int, rsi: float, trend: str) -> int:
    """1–10 arası sinyal gücü hesapla."""
    base = 5
    # RSI confluence
    if signal_int > 0 and rsi < 30:
        base += 2  # Aşırı satımda AL → güçlü
    elif signal_int > 0 and rsi > 70:
        base -= 2  # Aşırı alımda AL → zayıf
    elif signal_int < 0 and rsi > 70:
        base += 2  # Aşırı alımda SAT → güçlü
    elif signal_int < 0 and rsi < 30:
        base -= 2  # Aşırı satımda SAT → zayıf

    # Trend confluence
    if signal_int > 0 and trend == "BULLISH":
        base += 1
    elif signal_int > 0 and trend == "BEARISH":
        base -= 1
    elif signal_int < 0 and trend == "BEARISH":
        base += 1
    elif signal_int < 0 and trend == "BULLISH":
        base -= 1

    return max(1, min(10, base))


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
        self.skipped_untrusted = 0
        self.last_skip_reason: str | None = None
        self.last_lgbm_prob: float | None = None
        self._strategy_store = StrategyStore()

    @staticmethod
    def _trusted_metadata(metadata: dict[str, Any] | None) -> tuple[bool, str]:
        if not metadata:
            return False, "Veri metadata bilgisi yok; sinyal üretilmedi."
        status = str(metadata.get("status", "")).lower()
        is_real = bool(metadata.get("is_real", False))
        source = str(metadata.get("source") or metadata.get("provider_name") or "")
        if not is_real:
            return False, f"{source or 'Veri kaynağı'} gerçek veri olarak işaretlenmedi."
        if status not in {"ok", "live"}:
            return False, f"Veri durumu güvenli değil: {status or 'bilinmiyor'}."
        return True, ""

    async def evaluate(
        self,
        symbol: str,
        interval: str,
        bars: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Worker ``on_bar`` hook entry point.

        ``bars`` worker'ın az önce yazdığı son barlardır. Cache'in tamamı
        zaten yazılmış olduğu için biz cache'ten son ``lookback_bars``
        kadarını okuruz.
        """
        del bars  # bilgi amaçlı; cache zaten güncel
        ok, reason = self._trusted_metadata(metadata)
        if not ok:
            self.skipped_untrusted += 1
            self.last_skip_reason = reason
            self.evaluated_count += 1
            logger.warning("signal_generator: %s %s/%s", reason, symbol, interval)
            return
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

        # Teknik gösterge hesaplamaları (tüm stratejiler için ortak)
        closes = df["close"]
        rsi = _compute_rsi(closes)
        atr = _compute_atr(df)
        trend = _trend_direction(closes)
        volatility = (atr / price * 100) if price > 0 else 0  # ATR% olarak
        lgbm_prob = self._lgbm_probability(raw_bars)

        portfolio = Portfolio(initial_capital=self.config.capital)
        individual_signals: list[dict[str, Any]] = []
        buy_count = 0
        sell_count = 0

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

            if signal_int > 0:
                buy_count += 1
            else:
                sell_count += 1

            strength = _compute_strength(signal_int, rsi, trend)
            sig_type = "BUY" if signal_int > 0 else "SELL"
            metadata = {
                "rsi": round(rsi, 1),
                "trend": trend,
                "atr": round(atr, 4),
                "volatility_pct": round(volatility, 2),
            }
            if lgbm_prob is not None:
                metadata["lgbm_prob"] = lgbm_prob

            individual_signals.append(
                {
                    "symbol": canonical,
                    "signal_type": sig_type,
                    "price": price,
                    "strategy_id": name,
                    "reason": f"{name}: {sig_type} @ {price:.2f}",
                    "strength": strength,
                    "interval": interval,
                    "metadata": metadata,
                }
            )

        # Konsensüs sinyali — 5+ strateji aynı yönde ise STRONG sinyal ekle
        threshold = self.config.consensus_threshold
        total_strategies = len(self._strategy_names())

        if buy_count >= threshold:
            consensus_strength = min(10, 5 + buy_count)
            metadata = {
                "rsi": round(rsi, 1),
                "trend": trend,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "total_strategies": total_strategies,
                "consensus_ratio": round(buy_count / max(total_strategies, 1), 2),
            }
            if lgbm_prob is not None:
                metadata["lgbm_prob"] = lgbm_prob
            individual_signals.append(
                {
                    "symbol": canonical,
                    "signal_type": "STRONG_BUY",
                    "price": price,
                    "strategy_id": "_consensus",
                    "reason": f"KONSENSÜS: {buy_count}/{total_strategies} strateji AL sinyali",
                    "strength": consensus_strength,
                    "interval": interval,
                    "metadata": metadata,
                }
            )
        elif sell_count >= threshold:
            consensus_strength = min(10, 5 + sell_count)
            metadata = {
                "rsi": round(rsi, 1),
                "trend": trend,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "total_strategies": total_strategies,
                "consensus_ratio": round(sell_count / max(total_strategies, 1), 2),
            }
            if lgbm_prob is not None:
                metadata["lgbm_prob"] = lgbm_prob
            individual_signals.append(
                {
                    "symbol": canonical,
                    "signal_type": "STRONG_SELL",
                    "price": price,
                    "strategy_id": "_consensus",
                    "reason": f"KONSENSÜS: {sell_count}/{total_strategies} strateji SAT sinyali",
                    "strength": consensus_strength,
                    "interval": interval,
                    "metadata": metadata,
                }
            )

        individual_signals.extend(
            self._compute_active_paper_spec_signals(canonical, interval, df, price)
        )

        return individual_signals

    def _compute_active_paper_spec_signals(
        self,
        symbol: str,
        interval: str,
        df: pd.DataFrame,
        price: float,
    ) -> list[dict[str, Any]]:
        """Kayıtlı strategy_spec paper aktivasyonlarını canlı sinyale çevir.

        Paper executor bugün long-only BUY/SELL uygular. Bu nedenle aktif
        spec'lerin short_entry/short_exit kuralları canlı paper emrine
        çevrilmez; gerçek emir güvenliği açısından short yalnızca backtest
        simülasyonunda kalır.
        """
        out: list[dict[str, Any]] = []
        try:
            activations = self._strategy_store.list_paper_activations(active_only=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("paper activation listesi okunamadı: %s", exc)
            return out

        for activation in activations:
            if activation.symbol != symbol or activation.interval != interval:
                continue
            record = self._strategy_store.get_strategy(activation.strategy_record_id)
            if record is None:
                continue
            spec = record.params.get("strategy_spec")
            if not isinstance(spec, dict):
                continue
            try:
                rules = evaluate_strategy_rules(spec, df)
            except Exception as exc:  # noqa: BLE001
                logger.warning("paper spec sinyali üretilemedi: %s", exc)
                continue
            last_index = len(df) - 1
            signal_type = ""
            reason_key = ""
            if bool(rules["long_entry"].iloc[last_index]):
                signal_type = "BUY"
                reason_key = "long_entry"
            elif bool(rules["long_exit"].iloc[last_index]):
                signal_type = "SELL"
                reason_key = "long_exit"
            if not signal_type:
                continue
            out.append(
                {
                    "symbol": symbol,
                    "signal_type": signal_type,
                    "price": price,
                    "strategy_id": f"paper_spec_{record.id}",
                    "reason": f"{record.name}: {reason_key} @ {price:.2f}",
                    "strength": 6,
                    "interval": interval,
                    "metadata": {
                        "source": "strategy_lab",
                        "strategy_record_id": record.id,
                        "activation_id": activation.id,
                        "report_id": activation.report_id,
                    },
                }
            )
        return out

    def _lgbm_probability(self, bars: list[dict[str, Any]]) -> float | None:
        model_path = getenv("LIGHTGBM_MODEL_PATH")
        if not model_path:
            self.last_lgbm_prob = None
            return None
        probability = lightgbm_model.predict_latest_probability(bars, model_path)
        self.last_lgbm_prob = round(probability, 4) if probability is not None else None
        return self.last_lgbm_prob

    def stats(self) -> dict[str, Any]:
        return {
            "evaluated": self.evaluated_count,
            "signals_emitted": self.signal_count,
            "errors": self.error_count,
            "last_error": self.last_error,
            "skipped_untrusted": self.skipped_untrusted,
            "last_skip_reason": self.last_skip_reason,
            "last_lgbm_prob": self.last_lgbm_prob,
            "lgbm_model_configured": bool(getenv("LIGHTGBM_MODEL_PATH")),
            "strategies": self._strategy_names(),
        }


def utc_iso_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

"""Strategy catalog presets for the StrategySpec DSL."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from quant_engine.strategy.spec import RULE_NAMES

StrategyCategory = Literal[
    "momentum",
    "trend_following",
    "mean_reversion",
    "breakout",
    "moving_average",
    "hybrid",
    "ml",
]

CATEGORIES: tuple[StrategyCategory, ...] = (
    "momentum",
    "trend_following",
    "mean_reversion",
    "breakout",
    "moving_average",
    "hybrid",
    "ml",
)


@dataclass(frozen=True)
class StrategyPreset:
    id: str
    label: str
    category: StrategyCategory
    expected_market: str
    suggested_timeframes: tuple[str, ...]
    min_bars: int
    suggested_stop_pct: float
    suggested_take_profit_pct: float
    repaint_risk: str
    liquidity_need: str
    description: str
    rules: dict[str, str]

    def metadata(self) -> dict[str, Any]:
        """Return frontend-safe catalog metadata without StrategySpec rules."""
        data = asdict(self)
        data.pop("rules")
        data["suggested_timeframes"] = list(self.suggested_timeframes)
        return data

    def to_strategy_spec(self) -> dict[str, Any]:
        """Convert the preset into the existing StrategySpec dict shape."""
        rules = {name: str(self.rules.get(name, "")).strip() for name in RULE_NAMES}
        if not any(rules.values()):
            raise ValueError(f"Strategy preset {self.id!r} has no rules")
        return {
            "name": self.label,
            "label": self.label,
            "preset_id": self.id,
            "category": self.category,
            "rules": rules,
            "risk": {
                "stop_loss_pct": self.suggested_stop_pct,
                "take_profit_pct": self.suggested_take_profit_pct,
            },
        }

    def to_dict(self, *, include_spec: bool = False) -> dict[str, Any]:
        """Return metadata, optionally enriched with its StrategySpec payload."""
        data = self.metadata()
        if include_spec:
            data["strategy_spec"] = self.to_strategy_spec()
        return data


_PRESETS: tuple[StrategyPreset, ...] = (
    StrategyPreset(
        id="momentum_rsi_macd",
        label="RSI MACD Momentum",
        category="momentum",
        expected_market="Directional markets with expanding participation",
        suggested_timeframes=("1h", "4h", "1d"),
        min_bars=120,
        suggested_stop_pct=0.04,
        suggested_take_profit_pct=0.09,
        repaint_risk="low",
        liquidity_need="medium",
        description="Follows upside momentum when RSI strength agrees with MACD trend.",
        rules={
            "long_entry": "RSI(C,14) > 55 AND MACD_LINE(C,12,26,9) > MACD_SIGNAL(C,12,26,9)",
            "long_exit": "RSI(C,14) < 45 OR CROSS_DOWN(MACD_LINE(C,12,26,9), MACD_SIGNAL(C,12,26,9))",
        },
    ),
    StrategyPreset(
        id="momentum_vwap_volume",
        label="VWAP Volume Momentum",
        category="momentum",
        expected_market="Liquid intraday symbols with sustained volume",
        suggested_timeframes=("15m", "30m", "1h"),
        min_bars=90,
        suggested_stop_pct=0.025,
        suggested_take_profit_pct=0.055,
        repaint_risk="low",
        liquidity_need="high",
        description="Requires price above VWAP with RSI and volume confirmation.",
        rules={
            "long_entry": "C > VWAP() AND RSI(C,14) > 55 AND V > SMA(V,20)",
            "long_exit": "C < VWAP() OR RSI(C,14) < 48",
        },
    ),
    StrategyPreset(
        id="trend_ema_20_50",
        label="EMA 20/50 Trend Follow",
        category="trend_following",
        expected_market="Persistent uptrends with clean pullbacks",
        suggested_timeframes=("4h", "1d"),
        min_bars=140,
        suggested_stop_pct=0.05,
        suggested_take_profit_pct=0.12,
        repaint_risk="low",
        liquidity_need="medium",
        description="Enters when the fast EMA crosses above the medium EMA.",
        rules={
            "long_entry": "CROSS_UP(EMA(C,20), EMA(C,50))",
            "long_exit": "CROSS_DOWN(EMA(C,20), EMA(C,50)) OR RSI(C,14) < 45",
        },
    ),
    StrategyPreset(
        id="trend_macd_ema_200",
        label="MACD EMA 200 Trend",
        category="trend_following",
        expected_market="Large-cap or index markets with trend regime filters",
        suggested_timeframes=("4h", "1d", "1w"),
        min_bars=260,
        suggested_stop_pct=0.06,
        suggested_take_profit_pct=0.14,
        repaint_risk="low",
        liquidity_need="medium",
        description="Trades MACD strength only while price remains above the 200 EMA.",
        rules={
            "long_entry": "C > EMA(C,200) AND CROSS_UP(MACD_LINE(C,12,26,9), MACD_SIGNAL(C,12,26,9))",
            "long_exit": "C < EMA(C,200) OR CROSS_DOWN(MACD_LINE(C,12,26,9), MACD_SIGNAL(C,12,26,9))",
        },
    ),
    StrategyPreset(
        id="mean_reversion_rsi_bollinger",
        label="RSI Bollinger Reversion",
        category="mean_reversion",
        expected_market="Range-bound markets with repeated overextension",
        suggested_timeframes=("1h", "4h", "1d"),
        min_bars=120,
        suggested_stop_pct=0.035,
        suggested_take_profit_pct=0.06,
        repaint_risk="low",
        liquidity_need="medium",
        description="Looks for oversold closes below the lower Bollinger band.",
        rules={
            "long_entry": "C < BB_LOWER(C,20,2) AND RSI(C,14) < 35",
            "long_exit": "C > BB_MID(C,20,2) OR RSI(C,14) > 55",
        },
    ),
    StrategyPreset(
        id="mean_reversion_vwap_rsi",
        label="VWAP RSI Reversion",
        category="mean_reversion",
        expected_market="Liquid intraday markets that revert to VWAP",
        suggested_timeframes=("5m", "15m", "30m"),
        min_bars=80,
        suggested_stop_pct=0.02,
        suggested_take_profit_pct=0.04,
        repaint_risk="low",
        liquidity_need="high",
        description="Buys below VWAP when RSI shows short-term exhaustion.",
        rules={
            "long_entry": "C < VWAP() AND RSI(C,14) < 40",
            "long_exit": "C >= VWAP() OR RSI(C,14) > 55",
        },
    ),
    StrategyPreset(
        id="breakout_donchian_volume",
        label="Donchian Volume Breakout",
        category="breakout",
        expected_market="Consolidations resolving into high-volume breakouts",
        suggested_timeframes=("1h", "4h", "1d"),
        min_bars=100,
        suggested_stop_pct=0.045,
        suggested_take_profit_pct=0.1,
        repaint_risk="low",
        liquidity_need="high",
        description="Uses fresh closing highs with volume above its recent average.",
        rules={
            "long_entry": "C >= HIGHEST(C,20) AND V > SMA(V,20)",
            "long_exit": "C < LOWEST(C,10) OR C < EMA(C,20)",
        },
    ),
    StrategyPreset(
        id="breakout_bollinger_expansion",
        label="Bollinger Expansion Breakout",
        category="breakout",
        expected_market="Volatility expansion after compression",
        suggested_timeframes=("30m", "1h", "4h"),
        min_bars=120,
        suggested_stop_pct=0.04,
        suggested_take_profit_pct=0.085,
        repaint_risk="low",
        liquidity_need="medium",
        description="Confirms upper-band breakouts with above-average volume.",
        rules={
            "long_entry": "C > BB_UPPER(C,20,2) AND V > SMA(V,20)",
            "long_exit": "C < BB_MID(C,20,2) OR RSI(C,14) < 45",
        },
    ),
    StrategyPreset(
        id="moving_average_sma_cross",
        label="SMA 20/50 Cross",
        category="moving_average",
        expected_market="Broad trend transitions with moderate noise",
        suggested_timeframes=("4h", "1d"),
        min_bars=120,
        suggested_stop_pct=0.05,
        suggested_take_profit_pct=0.11,
        repaint_risk="low",
        liquidity_need="medium",
        description="Classic moving-average crossover using 20 and 50 period SMAs.",
        rules={
            "long_entry": "CROSS_UP(SMA(C,20), SMA(C,50))",
            "long_exit": "CROSS_DOWN(SMA(C,20), SMA(C,50))",
        },
    ),
    StrategyPreset(
        id="moving_average_ema_pullback",
        label="EMA Pullback Continuation",
        category="moving_average",
        expected_market="Uptrends with shallow pullbacks to fast averages",
        suggested_timeframes=("1h", "4h", "1d"),
        min_bars=100,
        suggested_stop_pct=0.035,
        suggested_take_profit_pct=0.075,
        repaint_risk="low",
        liquidity_need="medium",
        description="Requires price above the 50 EMA and a recovery through the 20 EMA.",
        rules={
            "long_entry": "C > EMA(C,50) AND CROSS_UP(C, EMA(C,20)) AND RSI(C,14) > 50",
            "long_exit": "CROSS_DOWN(C, EMA(C,20)) OR C < EMA(C,50)",
        },
    ),
    StrategyPreset(
        id="hybrid_trend_reversion",
        label="Trend Filtered Reversion",
        category="hybrid",
        expected_market="Bullish regimes with mean-reverting pullbacks",
        suggested_timeframes=("1h", "4h", "1d"),
        min_bars=240,
        suggested_stop_pct=0.04,
        suggested_take_profit_pct=0.08,
        repaint_risk="low",
        liquidity_need="medium",
        description="Combines a 200 EMA regime filter with Bollinger and RSI pullback logic.",
        rules={
            "long_entry": "C > EMA(C,200) AND C < BB_MID(C,20,2) AND RSI(C,14) < 45",
            "long_exit": "C > BB_UPPER(C,20,2) OR RSI(C,14) > 65",
        },
    ),
    StrategyPreset(
        id="ml_feature_proxy_regime",
        label="ML Feature Proxy Regime",
        category="ml",
        expected_market="Feature-rich liquid markets suited for model prototyping",
        suggested_timeframes=("30m", "1h", "4h"),
        min_bars=220,
        suggested_stop_pct=0.045,
        suggested_take_profit_pct=0.095,
        repaint_risk="medium",
        liquidity_need="high",
        description="A deterministic proxy for ML-style features: trend, momentum, and liquidity.",
        rules={
            "long_entry": "C > EMA(C,100) AND MACD_HIST(C,12,26,9) > 0 AND RSI(C,14) > 50 AND V > SMA(V,30)",
            "long_exit": "MACD_HIST(C,12,26,9) < 0 OR RSI(C,14) < 45 OR C < EMA(C,100)",
        },
    ),
)

_PRESETS_BY_ID: dict[str, StrategyPreset] = {preset.id: preset for preset in _PRESETS}


def list_strategy_presets(*, include_spec: bool = False) -> list[dict[str, Any]]:
    """List all strategy presets as JSON-compatible dictionaries."""
    return [preset.to_dict(include_spec=include_spec) for preset in _PRESETS]


def get_strategy_preset(preset_id: str) -> dict[str, Any]:
    """Return one strategy preset as metadata plus StrategySpec payload."""
    try:
        preset = _PRESETS_BY_ID[preset_id]
    except KeyError as exc:
        raise KeyError(f"Unknown strategy preset: {preset_id}") from exc
    return preset.to_dict(include_spec=True)


def preset_to_strategy_spec(preset_id: str) -> dict[str, Any]:
    """Return only the StrategySpec payload for a catalog preset."""
    try:
        return _PRESETS_BY_ID[preset_id].to_strategy_spec()
    except KeyError as exc:
        raise KeyError(f"Unknown strategy preset: {preset_id}") from exc


__all__ = [
    "CATEGORIES",
    "StrategyCategory",
    "StrategyPreset",
    "get_strategy_preset",
    "list_strategy_presets",
    "preset_to_strategy_spec",
]

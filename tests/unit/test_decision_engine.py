"""Strateji karar motoru testleri."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_engine.strategy.decision_engine import (
    IndicatorSnapshot,
    analyze_indicator_snapshot,
    analyze_market_data,
)


def _snapshot(**overrides) -> IndicatorSnapshot:
    values = {
        "symbol": "THYAO",
        "timeframe": "Günlük",
        "latest_time": "2026-04-24 18:10",
        "current_price": 100.5,
        "volume": 1_000_000,
        "ema200": 90.0,
        "bb_lower": 100.0,
        "bb_middle": 108.0,
        "bb_upper": 116.0,
        "rsi14": 33.0,
        "prev_rsi14": 28.0,
    }
    values.update(overrides)
    return IndicatorSnapshot(**values)


def test_decision_engine_rejects_non_real_data():
    report = analyze_indicator_snapshot(
        _snapshot(),
        is_real_data=False,
        source_label="Test verisi",
    )

    assert report.decision == "VERİ YETERSİZ"
    assert "gerçek dışı" in report.to_log_text().lower()


def test_indicator_fusion_buy_requires_trend_volatility_and_momentum():
    report = analyze_indicator_snapshot(
        _snapshot(),
        is_real_data=True,
        source_label="Yahoo Finance",
    )

    assert report.decision == "AL"
    assert "EMA 200" in report.trend_control
    assert "Bollinger" in report.volatility_momentum
    assert "RSI" in report.volatility_momentum
    assert "99,00" in report.stop_loss


def test_no_single_indicator_signal_when_rsi_does_not_confirm():
    report = analyze_indicator_snapshot(
        _snapshot(rsi14=48.0, prev_rsi14=47.0),
        is_real_data=True,
        source_label="Yahoo Finance",
    )

    assert report.decision == "BEKLE"


def test_sell_signal_when_upper_band_and_rsi_overheated():
    report = analyze_indicator_snapshot(
        _snapshot(
            current_price=115.5,
            ema200=95.0,
            bb_lower=90.0,
            bb_middle=103.0,
            bb_upper=116.0,
            rsi14=74.0,
            prev_rsi14=71.0,
        ),
        is_real_data=True,
        source_label="Yahoo Finance",
    )

    assert report.decision == "SAT"
    assert "pozisyon kapatma" in report.stop_loss


def test_market_data_rejects_missing_volume_column():
    data = pd.DataFrame({"close": np.linspace(100, 120, 220)})

    report = analyze_market_data(
        data,
        is_real_data=True,
        symbol="THYAO",
        timeframe="Günlük",
        source_label="Yahoo Finance",
    )

    assert report.decision == "VERİ YETERSİZ"
    assert "volume" in report.data_status


def test_market_data_rejects_short_history_for_ema200():
    data = pd.DataFrame(
        {
            "date": pd.bdate_range("2026-01-01", periods=60),
            "close": np.linspace(100, 120, 60),
            "volume": np.full(60, 1_000_000),
        }
    )

    report = analyze_market_data(
        data,
        is_real_data=True,
        symbol="THYAO",
        timeframe="Günlük",
        source_label="Yahoo Finance",
    )

    assert report.decision == "VERİ YETERSİZ"
    assert "201 bar" in report.data_status

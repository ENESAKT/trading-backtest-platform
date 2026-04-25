"""Grafik kurulum JSON motoru testleri."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_engine.strategy.blueprint_engine import build_strategy_blueprint
from quant_engine.strategy.indicators import ichimoku_cloud


def _realish_ohlcv(rows: int = 260) -> pd.DataFrame:
    close = pd.Series(np.linspace(100, 145, rows) + np.sin(np.arange(rows)) * 2)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + 1.5
    low = pd.concat([open_, close], axis=1).min(axis=1) - 1.5
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2025-01-01", periods=rows),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.linspace(1_000_000, 2_000_000, rows),
        }
    )


def test_ichimoku_cloud_returns_expected_components():
    data = _realish_ohlcv()

    cloud = ichimoku_cloud(data["high"], data["low"], data["close"])

    assert set(cloud) == {
        "tenkan_sen",
        "kijun_sen",
        "senkou_span_a",
        "senkou_span_b",
        "chikou_span",
    }
    assert cloud["tenkan_sen"].notna().sum() > 0
    assert cloud["senkou_span_a"].notna().sum() > 0


def test_blueprint_rejects_non_real_data_with_strict_top_level_keys():
    blueprint = build_strategy_blueprint(
        _realish_ohlcv(),
        is_real_data=False,
        symbol="THYAO",
        timeframe="Günlük",
        selected_indicators=["Ichimoku", "RSI 14"],
        source_label="Test verisi",
    )

    assert set(blueprint) == {
        "planlama_ve_analiz",
        "strateji_bilgileri",
        "grafik_kurulum_haritasi",
    }
    assert blueprint["strateji_bilgileri"]["strateji_adi"].startswith("Veri Yetersiz")
    assert "AL koşulu oluşturulmadı" in blueprint["strateji_bilgileri"]["al_kosulu"]


def test_blueprint_maps_indicators_to_main_and_subchart_layers():
    blueprint = build_strategy_blueprint(
        _realish_ohlcv(),
        is_real_data=True,
        symbol="THYAO",
        timeframe="Günlük",
        selected_indicators=[
            "Ichimoku",
            "SMA 50",
            "Bollinger Bands",
            "RSI 14",
            "MACD",
            "Hacim",
            "Sermaye Eğrisi",
            "Drawdown",
        ],
        source_label="Yahoo Finance",
    )

    overlays = blueprint["grafik_kurulum_haritasi"]["ana_grafik_overlay"]
    subcharts = blueprint["grafik_kurulum_haritasi"]["alt_pencereler_subcharts"]
    overlay_names = {item.get("isim") for item in overlays}
    subchart_names = {item["isim"] for item in subcharts}

    assert "Ichimoku Bulutu" in overlay_names
    assert "SMA 50" in overlay_names
    assert "Bollinger Bands" in overlay_names
    assert "AL / SAT Okları" in overlay_names
    assert "RSI" in subchart_names
    assert "MACD" in subchart_names
    assert "Hacim (Volume)" in subchart_names
    assert "Maksimum Düşüş / Drawdown" in subchart_names
    assert "Fiyat=" in blueprint["planlama_ve_analiz"]["arastirma_adimi"]


def test_blueprint_rejects_missing_ohlcv_columns():
    data = _realish_ohlcv().drop(columns=["volume"])

    blueprint = build_strategy_blueprint(
        data,
        is_real_data=True,
        symbol="THYAO",
        timeframe="Günlük",
        selected_indicators=["RSI 14", "Hacim"],
        source_label="Yahoo Finance",
    )

    assert blueprint["strateji_bilgileri"]["strateji_adi"].startswith("Veri Yetersiz")
    assert "volume" in blueprint["planlama_ve_analiz"]["arastirma_adimi"]

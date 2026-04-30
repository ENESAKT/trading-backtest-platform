from __future__ import annotations

from quant_engine.research.lightgbm_model import feature_rows_from_bars, readiness_from_bars


def test_feature_rows_include_binary_target():
    bars = [
        {"close": 100 + i, "volume": 1000 + i}
        for i in range(25)
    ]

    rows = feature_rows_from_bars(bars)

    assert rows
    assert {"return_1", "distance_sma20", "volume", "target_up"} <= set(rows[0])
    assert rows[0]["target_up"] == 1.0


def test_readiness_reports_insufficient_data():
    bars = [{"close": 100 + i, "volume": 1000} for i in range(40)]

    report = readiness_from_bars(bars, min_rows=100)

    assert report.status == "insufficient_data"
    assert report.rows < report.min_rows

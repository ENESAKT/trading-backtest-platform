from __future__ import annotations

from quant_engine.research.lightgbm_model import (
    feature_rows_from_bars,
    readiness_from_bars,
    train_lightgbm_classifier,
)


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


def test_training_does_not_write_fake_model_when_data_is_insufficient(tmp_path):
    bars = [{"close": 100 + i, "volume": 1000} for i in range(40)]
    model_path = tmp_path / "model.txt"

    result = train_lightgbm_classifier(bars, model_path=model_path, min_rows=100)

    assert result.status == "insufficient_data"
    assert not model_path.exists()

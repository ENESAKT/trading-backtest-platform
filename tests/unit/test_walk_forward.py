import pandas as pd
import pytest

from quant_engine.research.walk_forward import (
    WalkForwardAnalysis,
    generate_windows,
    run_walk_forward_analysis,
)


def deterministic_fixture() -> pd.DataFrame:
    close = [100, 101, 103, 106, 110, 115, 121, 128, 136, 145, 155, 166]
    return pd.DataFrame(
        {
            "close": close,
            "regime": [
                "train",
                "train",
                "train",
                "train",
                "oos",
                "oos",
                "train",
                "train",
                "train",
                "train",
                "oos",
                "oos",
            ],
        }
    )


def test_generate_windows_uses_exact_non_overlapping_oos_boundaries():
    windows = generate_windows(
        12,
        in_sample_bars=4,
        out_of_sample_bars=2,
        step_bars=4,
    )

    assert [window.to_dict() for window in windows] == [
        {
            "index": 0,
            "in_sample_start": 0,
            "in_sample_end": 4,
            "out_of_sample_start": 4,
            "out_of_sample_end": 6,
        },
        {
            "index": 1,
            "in_sample_start": 4,
            "in_sample_end": 8,
            "out_of_sample_start": 8,
            "out_of_sample_end": 10,
        },
    ]


def test_oos_data_is_never_passed_to_optimization_score():
    data = deterministic_fixture()
    candidates = [{"lookback": 1}, {"lookback": 2}]

    def score_func(params, in_sample):
        assert len(in_sample) == 4
        assert set(in_sample["regime"]) == {"train"}
        return params["lookback"]

    def oos_return_func(params, out_of_sample):
        assert len(out_of_sample) == 2
        assert set(out_of_sample["regime"]) == {"oos"}
        return params["lookback"] * 5.0

    report = run_walk_forward_analysis(
        data.iloc[:6],
        candidates,
        score_func,
        oos_return_func,
        in_sample_bars=4,
        out_of_sample_bars=2,
        step_bars=2,
    )

    assert report.selected_params == [{"lookback": 2}]
    assert report.out_of_sample_return_pct == [10.0]
    assert report.passed is True


def test_walk_forward_report_is_deterministic_with_fixed_fixture():
    data = deterministic_fixture()
    candidates = [{"bias": -1}, {"bias": 1}]

    def score_func(params, in_sample):
        return in_sample["close"].pct_change().sum() * 100 + params["bias"]

    def oos_return_func(params, out_of_sample):
        raw_return = (
            out_of_sample["close"].iloc[-1] / out_of_sample["close"].iloc[0]
            - 1
        ) * 100
        return raw_return * params["bias"]

    report = run_walk_forward_analysis(
        data,
        candidates,
        score_func,
        oos_return_func,
        in_sample_bars=4,
        out_of_sample_bars=2,
        step_bars=4,
    )

    as_dict = report.to_dict()

    assert len(report.windows) == 2
    assert report.selected_params == [{"bias": 1}, {"bias": 1}]
    assert report.in_sample_score == pytest.approx(
        [6.8928193790252825, 16.547969816744512]
    )
    assert report.out_of_sample_return_pct == pytest.approx(
        [4.545454545454541, 6.617647058823528]
    )
    assert report.total_oos_return_pct == pytest.approx(11.463903743315495)
    assert as_dict["walk_forward_efficiency"] == report.walk_forward_efficiency
    assert as_dict["passed"] is True


def test_custom_selection_function_can_choose_candidate():
    data = deterministic_fixture().iloc[:6]
    candidates = [{"lookback": 1}, {"lookback": 2}]

    def choose_lowest_score(scores):
        return min(scores, key=lambda item: item.score)

    report = run_walk_forward_analysis(
        data,
        candidates,
        lambda params, in_sample: params["lookback"],
        lambda params, out_of_sample: params["lookback"] * 10.0,
        in_sample_bars=4,
        out_of_sample_bars=2,
        step_bars=1,
        selection_func=choose_lowest_score,
    )

    assert report.selected_params == [{"lookback": 1}]
    assert report.in_sample_score == [1.0]
    assert report.out_of_sample_return_pct == [10.0]


def test_insufficient_data_returns_clear_warning():
    data = pd.DataFrame({"close": [100, 101, 102]})
    analysis = WalkForwardAnalysis(
        data,
        in_sample_bars=3,
        out_of_sample_bars=2,
        step_bars=1,
    )

    report = analysis.run(
        [{"x": 1}],
        lambda params, in_sample: 1.0,
        lambda params, out_of_sample: 1.0,
    )

    assert report.windows == []
    assert report.passed is False
    assert report.warnings == [
        "Insufficient data for walk-forward analysis: got 3 bars, need at least 5."
    ]

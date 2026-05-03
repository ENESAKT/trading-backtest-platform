"""
Walk-forward analysis utilities.

This module intentionally stays independent from the concrete backtest
engine. Callers provide scoring and out-of-sample return functions, so the
optimization step receives only in-sample data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

import pandas as pd


ParamSet = dict[str, Any]
ScoreFunction = Callable[[ParamSet, pd.DataFrame], float]
ReturnFunction = Callable[[ParamSet, pd.DataFrame], float]
SelectionFunction = Callable[[list["ParameterScore"]], "ParameterScore"]


@dataclass(frozen=True)
class WalkForwardConfig:
    """Bar counts used to build rolling walk-forward windows."""

    in_sample_bars: int
    out_of_sample_bars: int
    step_bars: int
    min_window_efficiency: float = 0.0

    def validate(self) -> None:
        """Validate positive window sizes."""
        if self.in_sample_bars <= 0:
            raise ValueError("in_sample_bars must be positive")
        if self.out_of_sample_bars <= 0:
            raise ValueError("out_of_sample_bars must be positive")
        if self.step_bars <= 0:
            raise ValueError("step_bars must be positive")


@dataclass(frozen=True)
class WalkForwardWindow:
    """Index boundaries for one walk-forward split."""

    index: int
    in_sample_start: int
    in_sample_end: int
    out_of_sample_start: int
    out_of_sample_end: int

    def in_sample(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive copy of the in-sample slice."""
        return data.iloc[self.in_sample_start : self.in_sample_end].copy()

    def out_of_sample(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive copy of the out-of-sample slice."""
        return data.iloc[self.out_of_sample_start : self.out_of_sample_end].copy()

    def to_dict(self) -> dict[str, int]:
        """Serialize window boundaries."""
        return {
            "index": self.index,
            "in_sample_start": self.in_sample_start,
            "in_sample_end": self.in_sample_end,
            "out_of_sample_start": self.out_of_sample_start,
            "out_of_sample_end": self.out_of_sample_end,
        }


@dataclass(frozen=True)
class ParameterScore:
    """In-sample optimization score for one parameter set."""

    params: ParamSet
    score: float


@dataclass
class WalkForwardWindowResult:
    """Result for a single walk-forward window."""

    window: WalkForwardWindow
    selected_params: ParamSet
    in_sample_score: float
    out_of_sample_return_pct: float
    walk_forward_efficiency: float
    passed: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize one window result."""
        return {
            "window": self.window.to_dict(),
            "selected_params": dict(self.selected_params),
            "in_sample_score": self.in_sample_score,
            "out_of_sample_return_pct": self.out_of_sample_return_pct,
            "walk_forward_efficiency": self.walk_forward_efficiency,
            "passed": self.passed,
            "warnings": list(self.warnings),
        }


@dataclass
class WalkForwardReport:
    """Aggregated walk-forward analysis report."""

    windows: list[WalkForwardWindowResult] = field(default_factory=list)
    selected_params: list[ParamSet] = field(default_factory=list)
    in_sample_score: list[float] = field(default_factory=list)
    out_of_sample_return_pct: list[float] = field(default_factory=list)
    walk_forward_efficiency: float = 0.0
    total_oos_return_pct: float = 0.0
    passed: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report model."""
        return {
            "windows": [window.to_dict() for window in self.windows],
            "selected_params": [dict(params) for params in self.selected_params],
            "in_sample_score": list(self.in_sample_score),
            "out_of_sample_return_pct": list(self.out_of_sample_return_pct),
            "walk_forward_efficiency": self.walk_forward_efficiency,
            "total_oos_return_pct": self.total_oos_return_pct,
            "passed": self.passed,
            "warnings": list(self.warnings),
        }


def generate_windows(
    data_length: int,
    *,
    in_sample_bars: int,
    out_of_sample_bars: int,
    step_bars: int,
) -> list[WalkForwardWindow]:
    """Generate rolling in-sample/out-of-sample windows."""
    config = WalkForwardConfig(
        in_sample_bars=in_sample_bars,
        out_of_sample_bars=out_of_sample_bars,
        step_bars=step_bars,
    )
    config.validate()

    windows: list[WalkForwardWindow] = []
    start = 0
    index = 0
    total_bars = in_sample_bars + out_of_sample_bars

    while start + total_bars <= data_length:
        in_end = start + in_sample_bars
        oos_end = in_end + out_of_sample_bars
        windows.append(
            WalkForwardWindow(
                index=index,
                in_sample_start=start,
                in_sample_end=in_end,
                out_of_sample_start=in_end,
                out_of_sample_end=oos_end,
            )
        )
        index += 1
        start += step_bars

    return windows


def select_best_score(scores: list[ParameterScore]) -> ParameterScore:
    """Select the parameter set with the highest in-sample score."""
    if not scores:
        raise ValueError("scores must not be empty")
    return max(scores, key=lambda item: item.score)


class WalkForwardAnalysis:
    """Run walk-forward analysis with caller-provided evaluation functions."""

    def __init__(
        self,
        data: pd.DataFrame,
        *,
        in_sample_bars: int,
        out_of_sample_bars: int,
        step_bars: int,
        min_window_efficiency: float = 0.0,
    ) -> None:
        self.data = data
        self.config = WalkForwardConfig(
            in_sample_bars=in_sample_bars,
            out_of_sample_bars=out_of_sample_bars,
            step_bars=step_bars,
            min_window_efficiency=min_window_efficiency,
        )
        self.config.validate()

    def windows(self) -> list[WalkForwardWindow]:
        """Return the generated WFA windows for this dataset."""
        return generate_windows(
            len(self.data),
            in_sample_bars=self.config.in_sample_bars,
            out_of_sample_bars=self.config.out_of_sample_bars,
            step_bars=self.config.step_bars,
        )

    def run(
        self,
        param_candidates: Iterable[ParamSet],
        score_func: ScoreFunction,
        out_of_sample_return_func: ReturnFunction,
        *,
        selection_func: SelectionFunction | None = None,
    ) -> WalkForwardReport:
        """Run WFA.

        The scoring function is called only with the in-sample slice. The
        out-of-sample slice is evaluated after parameter selection.
        """
        candidates = [dict(candidate) for candidate in param_candidates]
        warnings: list[str] = []

        if not candidates:
            warnings.append("No parameter candidates supplied.")
            return WalkForwardReport(warnings=warnings)

        windows = self.windows()
        required_bars = self.config.in_sample_bars + self.config.out_of_sample_bars
        if not windows:
            warnings.append(
                "Insufficient data for walk-forward analysis: "
                f"got {len(self.data)} bars, need at least {required_bars}."
            )
            return WalkForwardReport(warnings=warnings)

        selector = selection_func or select_best_score
        window_results: list[WalkForwardWindowResult] = []

        for window in windows:
            in_sample = window.in_sample(self.data)
            out_of_sample = window.out_of_sample(self.data)
            scores = [
                ParameterScore(params=params, score=float(score_func(params, in_sample)))
                for params in candidates
            ]
            selected = selector(scores)
            oos_return = float(
                out_of_sample_return_func(selected.params, out_of_sample)
            )
            efficiency = _walk_forward_efficiency(
                selected.score,
                oos_return,
            )
            passed = efficiency >= self.config.min_window_efficiency
            window_warnings: list[str] = []
            if not passed:
                window_warnings.append(
                    "Window failed minimum walk-forward efficiency: "
                    f"{efficiency:.4f} < {self.config.min_window_efficiency:.4f}."
                )

            window_results.append(
                WalkForwardWindowResult(
                    window=window,
                    selected_params=dict(selected.params),
                    in_sample_score=selected.score,
                    out_of_sample_return_pct=oos_return,
                    walk_forward_efficiency=efficiency,
                    passed=passed,
                    warnings=window_warnings,
                )
            )
            warnings.extend(window_warnings)

        oos_returns = [
            result.out_of_sample_return_pct for result in window_results
        ]
        efficiencies = [
            result.walk_forward_efficiency for result in window_results
        ]

        return WalkForwardReport(
            windows=window_results,
            selected_params=[
                dict(result.selected_params) for result in window_results
            ],
            in_sample_score=[
                result.in_sample_score for result in window_results
            ],
            out_of_sample_return_pct=oos_returns,
            walk_forward_efficiency=(
                sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
            ),
            total_oos_return_pct=_compound_returns(oos_returns),
            passed=bool(window_results)
            and all(result.passed for result in window_results),
            warnings=warnings,
        )


def run_walk_forward_analysis(
    data: pd.DataFrame,
    param_candidates: Iterable[ParamSet],
    score_func: ScoreFunction,
    out_of_sample_return_func: ReturnFunction,
    *,
    in_sample_bars: int,
    out_of_sample_bars: int,
    step_bars: int,
    min_window_efficiency: float = 0.0,
    selection_func: SelectionFunction | None = None,
) -> WalkForwardReport:
    """Convenience function for a one-shot WFA run."""
    analysis = WalkForwardAnalysis(
        data,
        in_sample_bars=in_sample_bars,
        out_of_sample_bars=out_of_sample_bars,
        step_bars=step_bars,
        min_window_efficiency=min_window_efficiency,
    )
    return analysis.run(
        param_candidates,
        score_func,
        out_of_sample_return_func,
        selection_func=selection_func,
    )


def _walk_forward_efficiency(
    in_sample_score: float,
    out_of_sample_return_pct: float,
) -> float:
    if in_sample_score == 0:
        return 0.0
    return out_of_sample_return_pct / abs(in_sample_score)


def _compound_returns(returns_pct: Sequence[float]) -> float:
    total = 1.0
    for return_pct in returns_pct:
        total *= 1 + (return_pct / 100.0)
    return (total - 1) * 100.0

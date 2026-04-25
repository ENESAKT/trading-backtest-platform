"""
Quant Engine — Grid Search Optimizer

Parametre uzayını sistematik tarayarak en iyi
strateji konfigürasyonunu bulur.

Özellikler:
    - Grid search (tam tarama)
    - Sonuç kaydetme
    - Overfitting uyarıları
    - Train/test split desteği
    - Progress ve cancel desteği
    - Walk-forward temel yapı

Kullanım:
    from quant_engine.research.optimizer import (
        GridSearchOptimizer,
    )

    optimizer = GridSearchOptimizer(engine, data, symbol)
    results = optimizer.run(
        strategy_cls=SmaCrossover,
        param_grid={
            "fast_period": [5, 10, 15],
            "slow_period": [20, 30, 50],
        },
    )
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd
from loguru import logger

from quant_engine.backtest.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestResult,
)
from quant_engine.backtest.metrics import (
    PerformanceMetrics,
    calculate_metrics,
)
from quant_engine.strategy.base import BaseStrategy


@dataclass
class OptimizationRun:
    """Tek bir parametre kombinasyonunun sonucu."""

    params: dict[str, Any]
    metrics: PerformanceMetrics
    result: BacktestResult
    duration_seconds: float = 0.0
    is_best: bool = False

    def summary_dict(self) -> dict[str, Any]:
        """Özet dictionary."""
        return {
            **self.params,
            "total_return_pct": self.metrics.total_return_pct,
            "cagr_pct": self.metrics.cagr_pct,
            "sharpe_ratio": self.metrics.sharpe_ratio,
            "sortino_ratio": self.metrics.sortino_ratio,
            "max_drawdown_pct": self.metrics.max_drawdown_pct,
            "win_rate": self.metrics.win_rate,
            "profit_factor": self.metrics.profit_factor,
            "total_trades": self.metrics.total_trades,
            "calmar_ratio": self.metrics.calmar_ratio,
            "duration_s": round(self.duration_seconds, 3),
        }


@dataclass
class OptimizationResult:
    """Grid search sonucu."""

    strategy_name: str
    runs: list[OptimizationRun] = field(
        default_factory=list
    )
    best_run: OptimizationRun | None = None
    total_combinations: int = 0
    completed_combinations: int = 0
    total_duration_seconds: float = 0.0
    ranking_metric: str = "sharpe_ratio"
    warnings: list[str] = field(default_factory=list)
    cancelled: bool = False

    def to_dataframe(self) -> pd.DataFrame:
        """Sonuçları DataFrame'e çevir."""
        if not self.runs:
            return pd.DataFrame()
        rows = [r.summary_dict() for r in self.runs]
        df = pd.DataFrame(rows)
        return df.sort_values(
            self.ranking_metric, ascending=False
        ).reset_index(drop=True)

    def top_n(self, n: int = 10) -> pd.DataFrame:
        """En iyi N sonucu göster."""
        return self.to_dataframe().head(n)

    def overfitting_check(self) -> list[str]:
        """
        Basit overfitting uyarıları.

        - Çok az trade ile yüksek Sharpe
        - En iyi parametre kümenin köşesinde
        - Sharpe > 3 uyarısı
        """
        warnings: list[str] = []

        if not self.best_run:
            return warnings

        best = self.best_run.metrics

        if best.sharpe_ratio > 3.0:
            warnings.append(
                f"⚠️ Sharpe {best.sharpe_ratio:.2f} > 3.0 "
                f"— overfitting riski yüksek!"
            )

        if best.total_trades < 5:
            warnings.append(
                f"⚠️ Sadece {best.total_trades} trade — "
                f"istatistiksel anlamlılık düşük."
            )

        if best.total_trades < 10 and best.win_rate > 80:
            warnings.append(
                "⚠️ Az trade + yüksek win rate — "
                "muhtemelen overfitting."
            )

        return warnings


class GridSearchOptimizer:
    """
    Grid Search optimizasyonu.

    Parametre uzayındaki tüm kombinasyonları test eder.
    """

    def __init__(
        self,
        config: BacktestConfig,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        timeframe: str = "1d",
    ):
        self.config = config
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self._cancelled = False
        self._progress_callback: (
            Callable[[int, int], None] | None
        ) = None

    def cancel(self):
        """Optimizasyonu iptal et."""
        self._cancelled = True

    def set_progress_callback(
        self, callback: Callable[[int, int], None]
    ):
        """Progress callback ayarla: fn(completed, total)."""
        self._progress_callback = callback

    def run(
        self,
        strategy_cls: type[BaseStrategy],
        param_grid: dict[str, list[Any]],
        ranking_metric: str = "sharpe_ratio",
        train_ratio: float | None = None,
    ) -> OptimizationResult:
        """
        Grid search çalıştır.

        Args:
            strategy_cls: Strateji sınıfı
            param_grid: Parametre ızgarası
                {"fast_period": [5,10], "slow_period": [20,30]}
            ranking_metric: Sıralama metriği
            train_ratio: Train/test split oranı (None=tümü)

        Returns:
            OptimizationResult: Tüm sonuçlar
        """
        self._cancelled = False

        # Parametre kombinasyonları oluştur
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        total = len(combinations)

        result = OptimizationResult(
            strategy_name=strategy_cls.name,
            total_combinations=total,
            ranking_metric=ranking_metric,
        )

        logger.info(
            f"🔍 Grid Search: {strategy_cls.name} | "
            f"{total} kombinasyon | "
            f"Sıralama: {ranking_metric}"
        )

        # Train/test split
        if train_ratio and 0 < train_ratio < 1:
            split_idx = int(len(self.data) * train_ratio)
            train_data = self.data.iloc[:split_idx].copy()
            test_data = self.data.iloc[split_idx:].copy()
            logger.info(
                f"📊 Train: {len(train_data)} bar | "
                f"Test: {len(test_data)} bar"
            )
        else:
            train_data = self.data
            test_data = None

        start_time = time.time()
        engine = BacktestEngine(self.config)

        for i, combo in enumerate(combinations):
            if self._cancelled:
                result.cancelled = True
                result.warnings.append(
                    f"Optimizasyon iptal edildi "
                    f"({i}/{total} tamamlandı)"
                )
                break

            params = dict(zip(keys, combo))

            # Parametre validasyonu
            try:
                strategy = strategy_cls(params=params)
                validation_errors = (
                    strategy.validate_params()
                )
                if validation_errors:
                    logger.debug(
                        f"⏭️ {params}: "
                        f"Geçersiz — {validation_errors}"
                    )
                    continue
            except (ValueError, KeyError) as e:
                logger.debug(
                    f"⏭️ {params}: Oluşturulamadı — {e}"
                )
                continue

            # Backtest çalıştır
            run_start = time.time()
            try:
                strategy.prepare(train_data)
                bt_result = engine.run(
                    train_data,
                    strategy.as_signal_func(),
                    symbol=self.symbol,
                )
                metrics = calculate_metrics(
                    bt_result.equity_curve,
                    bt_result.fills,
                    self.config.initial_capital,
                    timeframe=self.timeframe,
                    trades=bt_result.trades,
                )
            except Exception as e:
                logger.warning(
                    f"❌ {params}: Backtest hatası — {e}"
                )
                continue

            run_duration = time.time() - run_start

            opt_run = OptimizationRun(
                params=params,
                metrics=metrics,
                result=bt_result,
                duration_seconds=run_duration,
            )
            result.runs.append(opt_run)
            result.completed_combinations += 1

            if self._progress_callback:
                self._progress_callback(i + 1, total)

        result.total_duration_seconds = (
            time.time() - start_time
        )

        # En iyi sonucu bul
        if result.runs:
            result.runs.sort(
                key=lambda r: getattr(
                    r.metrics, ranking_metric, 0
                ),
                reverse=True,
            )
            result.best_run = result.runs[0]
            result.best_run.is_best = True

            # Overfitting kontrolü
            result.warnings.extend(
                result.overfitting_check()
            )

        logger.success(
            f"✅ Grid Search tamamlandı: "
            f"{result.completed_combinations}/{total} | "
            f"{result.total_duration_seconds:.1f}s"
        )

        if result.best_run:
            best = result.best_run
            logger.info(
                f"🏆 En iyi: {best.params} | "
                f"Sharpe: {best.metrics.sharpe_ratio:.2f} "
                f"| Return: "
                f"{best.metrics.total_return_pct:+.2f}%"
            )

        return result


class WalkForwardOptimizer:
    """
    Walk-Forward optimizasyon temel yapısı.

    Veriyi kayan pencerelerle böler:
    [train_1][test_1] → [train_2][test_2] → ...

    Her pencerede en iyi parametreleri bulur,
    test kısmında doğrular.
    """

    def __init__(
        self,
        config: BacktestConfig,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        n_splits: int = 5,
        train_ratio: float = 0.7,
    ):
        self.config = config
        self.data = data
        self.symbol = symbol
        self.n_splits = n_splits
        self.train_ratio = train_ratio

    def run(
        self,
        strategy_cls: type[BaseStrategy],
        param_grid: dict[str, list[Any]],
        ranking_metric: str = "sharpe_ratio",
    ) -> list[dict[str, Any]]:
        """
        Walk-forward optimizasyon çalıştır.

        Returns:
            list[dict]: Her split için train/test sonuçları
        """
        n_bars = len(self.data)
        split_size = n_bars // self.n_splits
        results: list[dict[str, Any]] = []

        logger.info(
            f"📊 Walk-Forward: {self.n_splits} split | "
            f"Train ratio: {self.train_ratio:.0%}"
        )

        for i in range(self.n_splits):
            start = i * split_size
            end = min(
                start + split_size, n_bars
            )
            window = self.data.iloc[start:end].copy()

            if len(window) < 20:
                continue

            train_end = int(
                len(window) * self.train_ratio
            )
            train = window.iloc[:train_end].copy()
            test = window.iloc[train_end:].copy()

            if len(train) < 10 or len(test) < 5:
                continue

            # Train'de optimize et
            optimizer = GridSearchOptimizer(
                self.config, train, self.symbol
            )
            opt_result = optimizer.run(
                strategy_cls,
                param_grid,
                ranking_metric,
            )

            if not opt_result.best_run:
                continue

            best_params = opt_result.best_run.params

            # Test'te doğrula
            strategy = strategy_cls(params=best_params)
            strategy.prepare(test)
            engine = BacktestEngine(self.config)
            test_result = engine.run(
                test,
                strategy.as_signal_func(),
                symbol=self.symbol,
            )
            test_metrics = calculate_metrics(
                test_result.equity_curve,
                test_result.fills,
                self.config.initial_capital,
                trades=test_result.trades,
            )

            results.append(
                {
                    "split": i + 1,
                    "best_params": best_params,
                    "train_sharpe": (
                        opt_result.best_run
                        .metrics.sharpe_ratio
                    ),
                    "test_sharpe": (
                        test_metrics.sharpe_ratio
                    ),
                    "train_return": (
                        opt_result.best_run
                        .metrics.total_return_pct
                    ),
                    "test_return": (
                        test_metrics.total_return_pct
                    ),
                    "train_bars": len(train),
                    "test_bars": len(test),
                }
            )

            logger.info(
                f"  Split {i+1}: "
                f"Train Sharpe={results[-1]['train_sharpe']:.2f} "
                f"Test Sharpe={results[-1]['test_sharpe']:.2f}"
            )

        return results

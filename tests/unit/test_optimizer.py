"""
Quant Engine — Optimizer Testleri

Test edilen:
- Grid Search temel çalışma
- Parametre validasyonu (geçersiz kombinasyonlar atlanır)
- Ranking metrikleri
- Overfitting uyarıları
- Walk-Forward temel yapı
- Cancel mekanizması
"""

import numpy as np
import pandas as pd
import pytest

from quant_engine.backtest.engine import BacktestConfig
from quant_engine.research.optimizer import (
    GridSearchOptimizer,
    WalkForwardOptimizer,
)


@pytest.fixture
def synth_data_200():
    """200 barlık yapay veri."""
    np.random.seed(42)
    n = 200
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    open_ = close + np.random.randn(n) * 0.5
    high = np.maximum(open_, close) + np.abs(
        np.random.randn(n)
    )
    low = np.minimum(open_, close) - np.abs(
        np.random.randn(n)
    )
    return pd.DataFrame(
        {
            "date": pd.bdate_range(
                "2023-01-02", periods=n
            ),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(
                100_000, 5_000_000, n
            ),
            "symbol": ["TEST"] * n,
        }
    )


@pytest.fixture
def opt_config():
    """Optimizer test config."""
    return BacktestConfig(
        initial_capital=100_000,
        commission_rate=0.001,
        slippage_bps=0,
        max_position_pct=1.0,
    )


class TestGridSearch:
    """Grid Search temel testleri."""

    def test_basic_grid_search(
        self, synth_data_200, opt_config
    ):
        """Basit grid search çalışır."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        optimizer = GridSearchOptimizer(
            opt_config, synth_data_200, "TEST"
        )
        result = optimizer.run(
            SmaCrossover,
            {
                "fast_period": [5, 10],
                "slow_period": [20, 30],
            },
        )

        assert result.total_combinations == 4
        assert result.completed_combinations > 0
        assert result.best_run is not None
        assert result.best_run.is_best is True

    def test_invalid_params_skipped(
        self, synth_data_200, opt_config
    ):
        """Geçersiz parametre kombinasyonları atlanır."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        optimizer = GridSearchOptimizer(
            opt_config, synth_data_200, "TEST"
        )
        result = optimizer.run(
            SmaCrossover,
            {
                "fast_period": [5, 30],  # 30 >= slow_period
                "slow_period": [20],
            },
        )

        # fast=30, slow=20 → validate_params hata verir
        assert result.completed_combinations == 1

    def test_result_to_dataframe(
        self, synth_data_200, opt_config
    ):
        """Sonuçlar DataFrame'e dönüşür."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        optimizer = GridSearchOptimizer(
            opt_config, synth_data_200, "TEST"
        )
        result = optimizer.run(
            SmaCrossover,
            {
                "fast_period": [5, 10],
                "slow_period": [20, 30],
            },
        )

        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "sharpe_ratio" in df.columns
        assert "fast_period" in df.columns
        assert len(df) == result.completed_combinations

    def test_ranking_by_custom_metric(
        self, synth_data_200, opt_config
    ):
        """Özel metrikle sıralama."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        optimizer = GridSearchOptimizer(
            opt_config, synth_data_200, "TEST"
        )
        result = optimizer.run(
            SmaCrossover,
            {
                "fast_period": [5, 10],
                "slow_period": [20, 30],
            },
            ranking_metric="total_return_pct",
        )

        assert (
            result.ranking_metric == "total_return_pct"
        )

    def test_cancel_mechanism(
        self, synth_data_200, opt_config
    ):
        """Cancel mekanizması çalışır."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        optimizer = GridSearchOptimizer(
            opt_config, synth_data_200, "TEST"
        )

        # İlk iterasyondan sonra iptal et
        def cancel_after_one(completed, total):
            if completed >= 1:
                optimizer.cancel()

        optimizer.set_progress_callback(
            cancel_after_one
        )

        result = optimizer.run(
            SmaCrossover,
            {
                "fast_period": [5, 10, 15],
                "slow_period": [20, 30, 50],
            },
        )

        assert result.cancelled is True
        assert result.completed_combinations < 9


class TestWalkForward:
    """Walk-Forward temel testleri."""

    def test_walk_forward_runs(
        self, synth_data_200, opt_config
    ):
        """Walk-Forward temel çalışma."""
        from quant_engine.strategy.examples.sma_crossover import (
            SmaCrossover,
        )

        wf = WalkForwardOptimizer(
            opt_config,
            synth_data_200,
            "TEST",
            n_splits=2,
            train_ratio=0.7,
        )
        results = wf.run(
            SmaCrossover,
            {
                "fast_period": [5, 10],
                "slow_period": [20, 30],
            },
        )

        assert len(results) > 0
        for r in results:
            assert "train_sharpe" in r
            assert "test_sharpe" in r
            assert "best_params" in r


class TestOverfitting:
    """Overfitting uyarı testleri."""

    def test_high_sharpe_warning(self):
        """Sharpe > 3 uyarı verir."""
        from quant_engine.backtest.metrics import (
            PerformanceMetrics,
        )
        from quant_engine.research.optimizer import (
            OptimizationResult,
            OptimizationRun,
        )

        fake_metrics = PerformanceMetrics(
            sharpe_ratio=4.5,
            total_trades=50,
            win_rate=60,
        )
        fake_run = OptimizationRun(
            params={"x": 1},
            metrics=fake_metrics,
            result=None,
        )

        result = OptimizationResult(
            strategy_name="test",
            best_run=fake_run,
        )
        warnings = result.overfitting_check()
        assert any("overfitting" in w for w in warnings)

    def test_few_trades_warning(self):
        """Az trade uyarı verir."""
        from quant_engine.backtest.metrics import (
            PerformanceMetrics,
        )
        from quant_engine.research.optimizer import (
            OptimizationResult,
            OptimizationRun,
        )

        fake_metrics = PerformanceMetrics(
            sharpe_ratio=1.5,
            total_trades=3,
            win_rate=100,
        )
        fake_run = OptimizationRun(
            params={"x": 1},
            metrics=fake_metrics,
            result=None,
        )

        result = OptimizationResult(
            strategy_name="test",
            best_run=fake_run,
        )
        warnings = result.overfitting_check()
        assert any(
            "istatistiksel" in w for w in warnings
        )

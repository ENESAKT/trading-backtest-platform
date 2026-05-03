"""``POST /api/backtest/run`` integration testi.

Cache'i sentetik 200 bar ile doldurup gerçek ``BacktestEngine`` üzerinden
endpoint cevabını doğrularız. Provider veya WS daemon başlatılmaz.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.api.quote_bus import QuoteBus
from backend.backtest.archive import BacktestArchive
from backend.data.cache import OHLCVCache
from backend.data.historical_store import HistoricalStore
from backend.workers import WorkerSupervisor
from quant_engine.data_pipeline.storage_manager import StorageManager
from quant_engine.strategy.persistence import StrategyStore


class _NoopDataService:
    def fetch_default_dashboard(self):
        return {"symbols": [], "metadata": {}}

    def fetch_chart(self, symbol: str, limit: int = 180):
        return {"symbol": symbol, "status": "ok", "bars": [], "quote": None, "metadata": {}}

    def fetch_candles(self, symbol: str, interval: str = "15m", limit: int = 500):
        return {"status": "ok", "bars": [], "metadata": {}, "symbol": symbol}


def _populate_cache(cache: OHLCVCache, symbol: str, interval: str, n: int = 200) -> None:
    """SMA crossover için cross üretebilen sinüsoidal dalga + uptrend."""
    bars: list[dict[str, Any]] = []
    for i in range(n):
        # 100 etrafında ±15 dalga + yavaş uptrend → birden fazla cross
        base = 100.0 + 0.05 * i
        wave = 15.0 * math.sin(i / 8.0)
        close = base + wave
        bars.append(
            {
                "time": 1_700_000_000 + i * 900,  # 15dk aralık
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1_000.0 + i,
            }
        )
    cache.upsert_bars(symbol, interval, bars)


def _build_client(tmp_path) -> tuple[TestClient, OHLCVCache]:
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    app = create_app(
        cache=cache,
        data_service=_NoopDataService(),
        supervisor=WorkerSupervisor([]),
        quote_bus=QuoteBus(),
        backtest_archive=BacktestArchive(tmp_path / "reports.sqlite3"),
        strategy_store=StrategyStore(tmp_path / "strategies.sqlite3"),
    )
    return TestClient(app), cache


def _historical_store(tmp_path, symbol: str = "THYAO", n: int = 120) -> HistoricalStore:
    storage = StorageManager(data_dir=str(tmp_path / "hist_data"))
    rows = []
    for i in range(n):
        close = 100.0 + i * 0.5 + 5.0 * math.sin(i / 6.0)
        rows.append({
            "date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=i),
            "open": close - 0.2,
            "high": close + 0.8,
            "low": close - 0.8,
            "close": close,
            "volume": 10_000 + i,
            "symbol": symbol,
        })
    storage.write_symbol_data(pd.DataFrame(rows), symbol, mode="overwrite")
    return HistoricalStore(storage=storage)


def test_strategies_endpoint_lists_blueprints(tmp_path):
    client, _ = _build_client(tmp_path)
    body = client.get("/api/backtest/strategies").json()
    ids = {s["id"] for s in body["strategies"]}
    assert ids == {
        "sma_crossover", "rsi_reversion", "bollinger_reversion", "buy_and_hold",
        "donchian_breakout", "macd_divergence", "supertrend", "mean_reversion_vwap",
        "lightgbm_probability",
    }
    sma = next(s for s in body["strategies"] if s["id"] == "sma_crossover")
    assert sma["default_params"] == {"fast_period": 10, "slow_period": 30}
    assert any(f["key"] == "fast_period" for f in sma["schema"])
    lgbm = next(s for s in body["strategies"] if s["id"] == "lightgbm_probability")
    assert lgbm["default_params"]["buy_threshold"] == 0.65


def test_backtest_run_returns_metrics_and_curve(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=200)

    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "BTCUSDT",
            "interval": "15m",
            "strategy_id": "sma_crossover",
            "params": {"fast_period": 5, "slow_period": 15},
            "capital": 50_000,
            "lookback_bars": 200,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["symbol"] == "BTCUSDT"
    assert body["strategy_id"] == "sma_crossover"
    assert body["params"] == {"fast_period": 5, "slow_period": 15}
    assert body["capital"] == 50_000.0

    metrics = body["metrics"]
    assert "final_equity" in metrics
    assert "total_return_pct" in metrics
    assert "max_drawdown_pct" in metrics
    assert metrics["total_trades"] >= 1  # sentetik dalga cross üretmeli

    assert len(body["equity_curve"]) == 200
    point = body["equity_curve"][0]
    assert {"time", "total_equity", "drawdown"} <= set(point.keys())
    wfa = body["walk_forward_report"]
    assert {"windows", "total_oos_return_pct", "walk_forward_efficiency", "passed", "warnings"} <= set(wfa)
    assert isinstance(wfa["windows"], list)
    assert wfa["warnings"]
    monte_carlo = body["monte_carlo_report"]
    assert {
        "median_final_equity",
        "p05_final_equity",
        "p95_final_equity",
        "probability_of_loss",
        "median_max_drawdown_pct",
        "p95_max_drawdown_pct",
        "warnings",
    } <= set(monte_carlo)
    assert "simulations" not in monte_carlo

    if body["trades"]:
        trade = body["trades"][0]
        assert trade["entry_price"] > 0
        # Fill tabanlı marker listesi tamamlanmış trade'leri kapsamalı.
        assert len(body["signals"]) >= 2 * len(body["trades"])
        assert {s["type"] for s in body["signals"]} <= {"BUY", "SELL"}
    assert body["run_id"]


def test_backtest_optimize_returns_stability_report(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "1d", n=200)

    resp = client.post(
        "/api/backtest/optimize",
        json={
            "symbol": "BTCUSDT",
            "interval": "1d",
            "strategy_id": "sma_crossover",
            "params": {},
            "param_grid": {
                "fast_period": [4, 5],
                "slow_period": [12, 15],
            },
            "lookback_bars": 200,
            "source_mode": "cache_only",
            "slippage_model": "fixed_tick",
            "slippage_tick": 0.01,
            "volume_limit_pct": 0.10,
            "volume_window": 3,
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["results"]
    stability = body["stability_report"]
    assert stability["param_keys"] == ["fast_period", "slow_period"]
    assert set(stability["best_params"]) == {"fast_period", "slow_period"}
    assert {"x_axis", "y_axis", "z_matrix"} <= set(stability["heatmap"])


def test_v2_candles_prefers_local_daily_parquet_and_writes_cache(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    app = create_app(
        cache=cache,
        data_service=_NoopDataService(),
        supervisor=WorkerSupervisor([]),
        quote_bus=QuoteBus(),
        backtest_archive=BacktestArchive(tmp_path / "reports.sqlite3"),
        strategy_store=StrategyStore(tmp_path / "strategies.sqlite3"),
        historical_store=_historical_store(tmp_path, "THYAO", n=90),
    )
    client = TestClient(app)

    resp = client.get(
        "/api/v2/candles",
        params={"symbol": "THYAO.IS", "interval": "1d", "limit": 80},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["symbol"] == "THYAO.IS"
    assert body["metadata"]["source"] == "local_parquet"
    assert body["metadata"]["is_real"] is True
    assert len(body["bars"]) == 80
    assert len(cache.get_window("THYAO.IS", "1d", limit=100)) == 80


def test_backtest_uses_local_daily_parquet_when_cache_is_empty(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    app = create_app(
        cache=cache,
        data_service=_NoopDataService(),
        supervisor=WorkerSupervisor([]),
        quote_bus=QuoteBus(),
        backtest_archive=BacktestArchive(tmp_path / "reports.sqlite3"),
        strategy_store=StrategyStore(tmp_path / "strategies.sqlite3"),
        historical_store=_historical_store(tmp_path, "THYAO", n=160),
    )
    client = TestClient(app)

    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "THYAO.IS",
            "interval": "1d",
            "strategy_id": "sma_crossover",
            "params": {"fast_period": 5, "slow_period": 20},
            "lookback_bars": 150,
            "source_mode": "cache_only",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data_source"]["source"] == "local_parquet"
    assert body["data_source"]["is_real"] is True
    assert body["lookback_bars"] == 150


def test_backtest_optimize_returns_stability_report(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=180)

    resp = client.post(
        "/api/backtest/optimize",
        json={
            "symbol": "BTCUSDT",
            "interval": "15m",
            "strategy_id": "strategy_spec",
            "strategy_spec": {
                "rules": {
                    "long_entry": "CROSS_UP(EMA(C,{fast}), EMA(C,{slow}))",
                    "long_exit": "CROSS_DOWN(EMA(C,{fast}), EMA(C,{slow}))",
                },
            },
            "param_grid": {"fast": [5, 8], "slow": [15, 20]},
            "lookback_bars": 180,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["results"]
    stability = body["stability_report"]
    assert stability["param_keys"] == ["fast", "slow"]
    assert set(stability["best_params"]) == {"fast", "slow"}
    assert {"x_axis", "y_axis", "z_matrix"} <= set(stability["heatmap"])


def test_backtest_scan_returns_scanner_v3_contract(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=160)

    resp = client.post(
        "/api/backtest/scan",
        json={
            "symbols": ["BTCUSDT"],
            "interval": "15m",
            "strategy_id": "sma_crossover",
            "params": {"fast_period": 5, "slow_period": 15},
            "lookback_bars": 160,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scanner_version"] == "v3"
    assert body["results"][0]["symbol"] == "BTCUSDT"


def test_backtest_v2_strategy_spec_short_and_archive_export(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "1d", n=180)

    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "BTCUSDT",
            "interval": "1d",
            "capital": 100_000,
            "commission_rate": 0.001,
            "slippage_bps": 2,
            "max_position_pct": 0.3,
            "allow_short": True,
            "source_mode": "cache_only",
            "strategy_spec": {
                "name": "EMA dönüş",
                "rules": {
                    "long_entry": "CROSS_UP(EMA(C,5), EMA(C,20))",
                    "long_exit": "CROSS_DOWN(EMA(C,5), EMA(C,20))",
                    "short_entry": "CROSS_DOWN(EMA(C,5), EMA(C,20))",
                    "short_exit": "CROSS_UP(EMA(C,5), EMA(C,20))",
                },
                "risk": {"stop_loss_pct": 3, "take_profit_pct": 8},
            },
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["strategy_id"] == "strategy_spec"
    assert body["metrics"]["final_equity"] > 0
    assert {"BUY", "SELL", "SHORT", "COVER"} & {s["type"] for s in body["signals"]}

    listed = client.get("/api/backtest/reports").json()["reports"]
    assert any(r["id"] == body["run_id"] for r in listed)

    exported = client.get(
        f"/api/backtest/reports/{body['run_id']}/export",
        params={"format": "trades_csv"},
    )
    assert exported.status_code == 200
    assert "entry_price" in exported.text


def test_backtest_v2_csv_import_validates_and_runs(tmp_path):
    client, _ = _build_client(tmp_path)
    rows = ["time,open,high,low,close,volume"]
    for i in range(80):
        close = 100 + i * 0.8
        rows.append(
            f"{1_700_000_000 + i * 86_400},{close},{close + 1},{close - 1},{close},{1000 + i}"
        )
    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "CSVTEST",
            "interval": "1d",
            "source_mode": "csv_import",
            "csv_text": "\n".join(rows),
            "strategy_spec": {
                "rules": {
                    "long_entry": "C > EMA(C,10)",
                    "long_exit": "C < EMA(C,10)",
                },
            },
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data_source"]["source"] == "csv_import"


def test_backtest_v2_csv_import_rejects_unsorted_rows(tmp_path):
    client, _ = _build_client(tmp_path)
    rows = ["time,open,high,low,close,volume"]
    for i in range(80):
        close = 100 + i * 0.8
        ts = 1_700_000_000 + (80 - i) * 86_400
        rows.append(f"{ts},{close},{close + 1},{close - 1},{close},{1000 + i}")
    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "CSVTEST",
            "interval": "1d",
            "source_mode": "csv_import",
            "csv_text": "\n".join(rows),
            "strategy_spec": {
                "rules": {
                    "long_entry": "C > EMA(C,10)",
                    "long_exit": "C < EMA(C,10)",
                },
            },
        },
    )
    assert resp.status_code == 400
    assert "tarih sırası" in resp.json()["detail"]


def test_backtest_run_rejects_unknown_strategy(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=120)
    resp = client.post(
        "/api/backtest/run",
        json={"symbol": "BTCUSDT", "strategy_id": "nope"},
    )
    assert resp.status_code == 400
    assert "nope" in resp.json()["detail"]


def test_backtest_run_rejects_insufficient_data(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=20)  # < MIN_BARS
    resp = client.post(
        "/api/backtest/run",
        json={"symbol": "BTCUSDT", "strategy_id": "sma_crossover"},
    )
    assert resp.status_code == 409
    assert "yetersiz" in resp.json()["detail"].lower()


def test_backtest_run_rejects_invalid_params(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=120)
    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "BTCUSDT",
            "strategy_id": "sma_crossover",
            "params": {"fast_period": 30, "slow_period": 10},  # fast >= slow
        },
    )
    assert resp.status_code == 400
    assert "fast_period" in resp.json()["detail"]


def test_backtest_run_rejects_unknown_param_key(tmp_path):
    client, cache = _build_client(tmp_path)
    _populate_cache(cache, "BTCUSDT", "15m", n=120)
    resp = client.post(
        "/api/backtest/run",
        json={
            "symbol": "BTCUSDT",
            "strategy_id": "sma_crossover",
            "params": {"bogus_key": 99},
        },
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "bogus_key" in detail or "bilinmeyen" in detail

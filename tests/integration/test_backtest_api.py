"""``POST /api/backtest/run`` integration testi.

Cache'i sentetik 200 bar ile doldurup gerçek ``BacktestEngine`` üzerinden
endpoint cevabını doğrularız. Provider veya WS daemon başlatılmaz.
"""

from __future__ import annotations

import math
from typing import Any

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.api.quote_bus import QuoteBus
from backend.backtest.archive import BacktestArchive
from backend.data.cache import OHLCVCache
from backend.workers import WorkerSupervisor
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

    if body["trades"]:
        trade = body["trades"][0]
        assert trade["entry_price"] > 0
        # Fill tabanlı marker listesi tamamlanmış trade'leri kapsamalı.
        assert len(body["signals"]) >= 2 * len(body["trades"])
        assert {s["type"] for s in body["signals"]} <= {"BUY", "SELL"}
    assert body["run_id"]


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

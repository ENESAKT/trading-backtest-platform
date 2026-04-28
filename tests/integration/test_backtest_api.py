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
from backend.data.cache import OHLCVCache
from backend.workers import WorkerSupervisor


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
    )
    return TestClient(app), cache


def test_strategies_endpoint_lists_blueprints(tmp_path):
    client, _ = _build_client(tmp_path)
    body = client.get("/api/backtest/strategies").json()
    ids = {s["id"] for s in body["strategies"]}
    assert ids == {"sma_crossover", "rsi_reversion", "bollinger_reversion", "buy_and_hold"}
    sma = next(s for s in body["strategies"] if s["id"] == "sma_crossover")
    assert sma["default_params"] == {"fast_period": 10, "slow_period": 30}
    assert any(f["key"] == "fast_period" for f in sma["schema"])


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
        # Her tamamlanmış trade için signals iki kayıt yayınlamalı.
        assert len(body["signals"]) == 2 * len(body["trades"])
        assert {s["type"] for s in body["signals"]} <= {"BUY", "SELL"}


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
    assert "bogus_key" in resp.json()["detail"].lower() or "bilinmeyen" in resp.json()["detail"].lower()

"""``BinanceKlineWorker`` mesaj parse ve persist testleri.

Gerçek WS bağlantısı kurulmaz; ``parse_kline_message`` saf fonksiyon olarak
test edilir, ``_persist`` ise event loop ile birlikte cache'in beklenen
çağrıyı aldığını doğrular.
"""

from __future__ import annotations

import json

import pytest

from backend.data.cache import OHLCVCache
from backend.workers.binance_ws import BinanceKlineWorker


def _kline_msg(symbol: str = "BTCUSDT", closed: bool = True) -> str:
    return json.dumps(
        {
            "stream": f"{symbol.lower()}@kline_15m",
            "data": {
                "e": "kline",
                "s": symbol,
                "k": {
                    "t": 1_700_000_000_000,  # ms
                    "T": 1_700_000_899_999,
                    "s": symbol,
                    "i": "15m",
                    "o": "100.0",
                    "h": "105.0",
                    "l": "99.0",
                    "c": "102.5",
                    "v": "1234.5",
                    "x": closed,
                },
            },
        }
    )


def test_parse_returns_bar_for_closed_kline():
    raw = _kline_msg(closed=True)
    result = BinanceKlineWorker.parse_kline_message(raw)
    assert result is not None
    symbol, bar = result
    assert symbol == "BTCUSDT"
    assert bar["time"] == 1_700_000_000  # ms→s
    assert bar["open"] == 100.0
    assert bar["high"] == 105.0
    assert bar["low"] == 99.0
    assert bar["close"] == 102.5
    assert bar["volume"] == 1234.5


def test_parse_skips_open_kline():
    raw = _kline_msg(closed=False)
    assert BinanceKlineWorker.parse_kline_message(raw) is None


def test_parse_handles_malformed_json():
    assert BinanceKlineWorker.parse_kline_message("not-json") is None
    assert BinanceKlineWorker.parse_kline_message(b"{") is None
    assert BinanceKlineWorker.parse_kline_message(json.dumps({"foo": "bar"})) is None


def test_build_url_combines_streams():
    cache = OHLCVCache(db_path=":memory:")  # path is fine; sqlite supports
    w = BinanceKlineWorker(
        cache=cache,
        symbols=["BTCUSDT", "ethusdt"],
        interval="15m",
    )
    url = w._build_url()
    assert url.startswith("wss://data-stream.binance.vision/stream?streams=")
    assert "btcusdt@kline_15m" in url
    assert "ethusdt@kline_15m" in url


def test_disconnect_updates_reconnect_health(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    w = BinanceKlineWorker(cache=cache, symbols=["BTCUSDT"], interval="15m")

    w._record_disconnect(ConnectionResetError("peer reset"), next_backoff=1.0)

    h = w.health()
    assert h.failures == 1
    assert "ConnectionResetError" in (h.last_error or "")
    assert h.metadata["reconnects"] == 1
    assert h.metadata["last_disconnect_at"] is not None
    assert h.metadata["backoff"]["max_seconds"] == w.MAX_BACKOFF


def test_backoff_jitter_stays_bounded(tmp_path, monkeypatch):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    w = BinanceKlineWorker(cache=cache, symbols=["BTCUSDT"], interval="15m")
    monkeypatch.setattr("backend.workers.binance_ws.random.uniform", lambda _a, _b: 0.2)

    assert w._with_jitter(1.0) == 1.2
    assert w._with_jitter(0.0) == 0


@pytest.mark.asyncio
async def test_persist_writes_bar_to_cache(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    w = BinanceKlineWorker(
        cache=cache, symbols=["BTCUSDT"], interval="15m"
    )
    bar = {
        "time": 1_700_000_000,
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 102.5,
        "volume": 1234.5,
    }
    await w._persist("BTCUSDT", bar)

    rows = cache.get_window("BTCUSDT", "15m")
    assert len(rows) == 1
    assert rows[0]["close"] == 102.5
    h = w.health()
    assert h.iterations == 1
    assert h.last_run_ok is not None


@pytest.mark.asyncio
async def test_persist_invokes_on_bar_hook(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "c.sqlite3")
    seen: list[tuple[str, str, list[dict]]] = []

    async def hook(symbol: str, interval: str, bars: list[dict]) -> None:
        seen.append((symbol, interval, bars))

    w = BinanceKlineWorker(
        cache=cache, symbols=["BTCUSDT"], interval="15m", on_bar=hook
    )
    bar = {
        "time": 1_700_000_000, "open": 1.0, "high": 1.0,
        "low": 1.0, "close": 1.0, "volume": 1.0,
    }
    await w._persist("BTCUSDT", bar)
    assert len(seen) == 1
    assert seen[0][0] == "BTCUSDT"
    assert seen[0][1] == "15m"
    assert seen[0][2][0]["close"] == 1.0

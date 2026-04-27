"""``backend.data.cache.OHLCVCache`` için unit testler."""

from __future__ import annotations

import pytest

from backend.data.cache import OHLCVCache


@pytest.fixture
def cache(tmp_path):
    return OHLCVCache(db_path=tmp_path / "ohlcv.sqlite3")


def _bar(t: int, c: float = 100.0, v: float = 10.0) -> dict:
    return {"time": t, "open": c, "high": c, "low": c, "close": c, "volume": v}


def test_upsert_and_get_window(cache):
    bars = [_bar(t=1000 + i * 60, c=100.0 + i) for i in range(5)]
    inserted = cache.upsert_bars("BTCUSDT", "1m", bars)
    assert inserted == 5

    fetched = cache.get_window("BTCUSDT", "1m")
    assert len(fetched) == 5
    assert [b["time"] for b in fetched] == [b["time"] for b in bars]
    assert fetched[0]["close"] == 100.0


def test_upsert_is_idempotent(cache):
    bars = [_bar(t=2000), _bar(t=2060)]
    cache.upsert_bars("THYAO.IS", "1m", bars)
    inserted = cache.upsert_bars("THYAO.IS", "1m", bars)
    assert inserted == 0  # ikinci çağrı yeni satır yazmaz

    fetched = cache.get_window("THYAO.IS", "1m")
    assert len(fetched) == 2


def test_get_window_filters_by_time_range(cache):
    bars = [_bar(t=t) for t in (100, 200, 300, 400, 500)]
    cache.upsert_bars("X", "5m", bars)

    sub = cache.get_window("X", "5m", start_ts=200, end_ts=400)
    assert [b["time"] for b in sub] == [200, 300, 400]


def test_get_window_with_limit_returns_most_recent(cache):
    bars = [_bar(t=t) for t in range(1, 11)]  # times 1..10
    cache.upsert_bars("X", "1m", bars)

    sub = cache.get_window("X", "1m", limit=3)
    # En yeni 3 bar (8, 9, 10), time ASC sıralı
    assert [b["time"] for b in sub] == [8, 9, 10]


def test_latest_bar_returns_none_when_empty(cache):
    assert cache.latest_bar("EMPTY", "1m") is None


def test_latest_bar_returns_newest(cache):
    cache.upsert_bars("X", "1m", [_bar(t=1), _bar(t=2), _bar(t=3)])
    latest = cache.latest_bar("X", "1m")
    assert latest is not None
    assert latest["time"] == 3


def test_stats_counts_rows_and_symbols(cache):
    cache.upsert_bars("AAA", "1m", [_bar(t=1), _bar(t=2)])
    cache.upsert_bars("BBB", "1m", [_bar(t=1)])
    stats = cache.stats()
    assert stats.rows == 3
    assert stats.distinct_symbols == 2
    assert stats.last_inserted_at is not None


def test_separate_intervals_kept_distinct(cache):
    cache.upsert_bars("X", "1m", [_bar(t=100)])
    cache.upsert_bars("X", "5m", [_bar(t=100)])
    assert len(cache.get_window("X", "1m")) == 1
    assert len(cache.get_window("X", "5m")) == 1
    assert cache.stats().rows == 2

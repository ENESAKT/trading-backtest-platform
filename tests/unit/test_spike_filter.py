"""``backend.data.spike_filter.filter_bars`` için unit testler."""

from __future__ import annotations

from backend.data.spike_filter import filter_bars


def _normal_bar(t: int, c: float, v: float = 100.0) -> dict:
    return {"time": t, "open": c, "high": c, "low": c, "close": c, "volume": v}


def test_returns_unchanged_for_small_input():
    bars = [_normal_bar(t=i, c=100.0 + i * 0.1) for i in range(5)]
    cleaned, report = filter_bars(bars)
    assert cleaned == bars
    assert report.winsorized == 0


def test_winsorizes_low_volume_spike():
    # 30 bar düz seyirde, sonunda DÜŞÜK hacimle %50 sıçrama → winsorize
    base_bars = [_normal_bar(t=i, c=100.0 + (i % 3) * 0.1, v=1_000.0) for i in range(30)]
    spike_bar = {
        "time": 30, "open": 100.0, "high": 150.0, "low": 100.0,
        "close": 150.0, "volume": 5.0,  # çok düşük hacim
    }
    cleaned, report = filter_bars(base_bars + [spike_bar])
    assert report.winsorized >= 1
    # Spike bar'ın close'u 150'den çok düşmüş olmalı
    assert cleaned[-1]["close"] < 110.0


def test_keeps_high_volume_spike_untouched():
    # 30 bar düz, sonunda YÜKSEK hacimle aynı %50 sıçrama → dokunma (Black Swan)
    base_bars = [_normal_bar(t=i, c=100.0 + (i % 3) * 0.1, v=1_000.0) for i in range(30)]
    big_news = {
        "time": 30, "open": 100.0, "high": 150.0, "low": 100.0,
        "close": 150.0, "volume": 50_000.0,  # çok yüksek hacim
    }
    cleaned, report = filter_bars(base_bars + [big_news])
    # Yüksek hacim varken bar'a dokunulmamalı
    assert cleaned[-1]["close"] == 150.0
    assert report.untouched_high_volume >= 1


def test_does_not_mutate_input():
    bars = [_normal_bar(t=i, c=100.0) for i in range(15)]
    snapshot = [dict(b) for b in bars]
    filter_bars(bars)
    assert bars == snapshot


def test_preserves_time_series_length():
    bars = [_normal_bar(t=i, c=100.0 + i * 0.05, v=500.0) for i in range(40)]
    bars.append({
        "time": 40, "open": 100.0, "high": 200.0, "low": 100.0,
        "close": 200.0, "volume": 1.0,
    })
    cleaned, _ = filter_bars(bars)
    assert len(cleaned) == len(bars)

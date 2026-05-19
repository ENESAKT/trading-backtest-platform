"""IQR + hacim ağırlıklı spike (dev fitil) filtresi.

Sprint 1.3 — düşük hacimli BIST hisselerinde ya da FX paritelerinde gelen
"dev fitil" anomalilerini Winsorize ederek temizler. Plan: planlama.md §6
ve eski MASTER_PLAN_v2.md §2.A.

## Algoritma

1. **Temel istatistikler:** Bar ``high``-``low`` aralıklarının ve close
   değişiminin medyanı + IQR.
2. **Outlier tanımı:** Close değişimi (Δ%) IQR sınırının ``IQR_MULT``
   katından fazla saparsa ya da bar ``high``/``low`` benzer şekilde sapıyorsa
   spike adayı.
3. **Hacim filtresi:**
   * **Sıfır / çok düşük hacim** + büyük fiyat sıçraması → kesin veri hatası
     → close, open, high, low Winsorize edilir (Q1−1.5·IQR — Q3+1.5·IQR
     bandına çekilir).
   * **Yüksek hacim** ile gelen sıçrama → "Black Swan" olabilir, dokunulmaz.
4. **Time-series boşluğu yok:** bar silinmez; sadece OHLC değerleri sınıra
   çekilir, ``volume`` korunur.

## Saf Python

NumPy/Pandas isteğe bağlı (cache pipeline test'lerinde mocklanabilsin diye).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Iterable, Sequence

Bar = dict[str, float | int]

IQR_MULT = 1.5
LOW_VOLUME_PERCENTILE = 0.20  # alt %20 hacim → "düşük hacim" sayılır
MIN_BARS = 10


@dataclass(frozen=True)
class SpikeReport:
    total_bars: int
    winsorized: int
    untouched_high_volume: int


def _quartiles(values: Sequence[float]) -> tuple[float, float, float, float]:
    """(q1, q2, q3, iqr) — saf Python."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q2 = statistics.median(sorted_vals)
    if n < 4:
        return q2, q2, q2, 0.0
    half = n // 2
    lower = sorted_vals[:half]
    upper = sorted_vals[half + 1 :] if n % 2 else sorted_vals[half:]
    q1 = statistics.median(lower)
    q3 = statistics.median(upper)
    return q1, q2, q3, q3 - q1


def _close_pct_changes(bars: Sequence[Bar]) -> list[float]:
    out: list[float] = []
    for prev, curr in zip(bars, bars[1:]):
        prev_close = float(prev["close"])
        if prev_close == 0:
            out.append(0.0)
            continue
        curr_close = float(curr["close"])
        out.append((curr_close - prev_close) / prev_close * 100.0)
    return out


def filter_bars(bars: Iterable[Bar]) -> tuple[list[Bar], SpikeReport]:
    """Bar dizisini IQR + hacim mantığıyla temizle.

    Dönen liste yeni dict'lerden oluşur; girdi mutate edilmez.
    """
    bar_list: list[Bar] = list(bars)
    n = len(bar_list)
    if n < MIN_BARS:
        # Çok küçük örneklem → istatistik güvenilmez; olduğu gibi dön.
        return [dict(b) for b in bar_list], SpikeReport(n, 0, 0)

    pct_changes = _close_pct_changes(bar_list)
    _, _, _, iqr_pct = _quartiles(pct_changes)
    pct_lower_bound = -IQR_MULT * iqr_pct if iqr_pct > 0 else float("-inf")
    pct_upper_bound = IQR_MULT * iqr_pct if iqr_pct > 0 else float("inf")

    volumes = [float(b["volume"]) for b in bar_list]
    sorted_vols = sorted(volumes)
    low_vol_idx = max(1, int(LOW_VOLUME_PERCENTILE * len(sorted_vols)))
    low_vol_threshold = sorted_vols[low_vol_idx - 1]

    cleaned: list[Bar] = []
    winsorized = 0
    untouched_high_volume = 0

    for i, bar in enumerate(bar_list):
        new_bar = dict(bar)
        if i == 0:
            cleaned.append(new_bar)
            continue

        prev_close = float(bar_list[i - 1]["close"])
        if prev_close == 0:
            cleaned.append(new_bar)
            continue
        change_pct = (float(bar["close"]) - prev_close) / prev_close * 100.0

        is_outlier = (
            change_pct < pct_lower_bound or change_pct > pct_upper_bound
        )
        if not is_outlier:
            cleaned.append(new_bar)
            continue

        bar_volume = float(bar["volume"])
        if bar_volume > low_vol_threshold:
            # Yüksek hacim — gerçek hareket olabilir, dokunma.
            untouched_high_volume += 1
            cleaned.append(new_bar)
            continue

        # Düşük hacimli sıçrama → veri hatası kabul; OHLC'yi sınıra çek.
        clamped_change = max(
            pct_lower_bound, min(pct_upper_bound, change_pct)
        )
        clamped_close = prev_close * (1.0 + clamped_change / 100.0)
        new_bar["close"] = clamped_close
        # Bar tutarlı kalsın diye open/high/low'u clamped_close civarına oturt.
        new_bar["open"] = prev_close
        new_bar["high"] = max(prev_close, clamped_close)
        new_bar["low"] = min(prev_close, clamped_close)
        # volume olduğu gibi korunur.
        winsorized += 1
        cleaned.append(new_bar)

    return cleaned, SpikeReport(
        total_bars=n,
        winsorized=winsorized,
        untouched_high_volume=untouched_high_volume,
    )

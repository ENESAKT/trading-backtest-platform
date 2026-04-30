"""LightGBM araştırma temeli.

Gerçek model eğitimi veri yeterliliği ve opsiyonel `lightgbm` paketine bağlıdır.
Bu modül eksik veri varken sessizce sahte model üretmez; readiness raporu döner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MLReadiness:
    status: str
    rows: int
    min_rows: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rows": self.rows,
            "min_rows": self.min_rows,
            "message": self.message,
        }


def feature_rows_from_bars(bars: list[dict[str, Any]]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    closes = [float(b["close"]) for b in bars if b.get("close") is not None]
    volumes = [float(b.get("volume") or 0) for b in bars if b.get("close") is not None]
    for i in range(20, len(closes) - 1):
        window = closes[i - 20:i]
        last = closes[i]
        prev = closes[i - 1]
        mean20 = sum(window) / len(window)
        rows.append(
            {
                "return_1": (last / prev - 1.0) if prev else 0.0,
                "distance_sma20": (last / mean20 - 1.0) if mean20 else 0.0,
                "volume": volumes[i] if i < len(volumes) else 0.0,
                "target_up": 1.0 if closes[i + 1] > last else 0.0,
            }
        )
    return rows


def readiness_from_bars(bars: list[dict[str, Any]], min_rows: int = 5_000) -> MLReadiness:
    rows = len(feature_rows_from_bars(bars))
    if rows < min_rows:
        return MLReadiness(
            status="insufficient_data",
            rows=rows,
            min_rows=min_rows,
            message="LightGBM eğitimi için yeterli etiketli bar birikmedi.",
        )
    try:
        import lightgbm  # noqa: F401
    except Exception:
        return MLReadiness(
            status="dependency_missing",
            rows=rows,
            min_rows=min_rows,
            message="Veri yeterli; lightgbm paketi kurulunca eğitim başlatılabilir.",
        )
    return MLReadiness(
        status="ready",
        rows=rows,
        min_rows=min_rows,
        message="Veri ve bağımlılık hazır; eğitim koşusu başlatılabilir.",
    )

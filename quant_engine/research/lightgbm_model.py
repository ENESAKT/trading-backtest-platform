"""LightGBM araştırma temeli.

Gerçek model eğitimi veri yeterliliği ve opsiyonel `lightgbm` paketine bağlıdır.
Bu modül eksik veri varken sessizce sahte model üretmez; readiness raporu döner.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

FEATURE_COLUMNS = ("return_1", "distance_sma20", "volume")


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


@dataclass
class MLTrainingResult:
    status: str
    rows: int
    min_rows: int
    message: str
    model_path: str = ""
    latest_probability: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rows": self.rows,
            "min_rows": self.min_rows,
            "message": self.message,
            "model_path": self.model_path,
            "latest_probability": self.latest_probability,
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


def _matrix(rows: list[dict[str, float]]) -> tuple[list[list[float]], list[float]]:
    x = [[float(row[col]) for col in FEATURE_COLUMNS] for row in rows]
    y = [float(row["target_up"]) for row in rows]
    return x, y


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


def train_lightgbm_classifier(
    bars: list[dict[str, Any]],
    model_path: str | Path,
    min_rows: int = 5_000,
    num_boost_round: int = 60,
) -> MLTrainingResult:
    """Yeterli gerçek veri varsa LightGBM binary classifier eğit.

    Veri veya paket yoksa sahte model üretmez; çağıran cron/Makefile'ın
    güvenle raporlayabileceği durum nesnesi döndürür.
    """
    rows = feature_rows_from_bars(bars)
    if len(rows) < min_rows:
        return MLTrainingResult(
            status="insufficient_data",
            rows=len(rows),
            min_rows=min_rows,
            message="LightGBM eğitimi için yeterli etiketli bar birikmedi.",
        )

    try:
        import lightgbm as lgb
    except Exception:
        return MLTrainingResult(
            status="dependency_missing",
            rows=len(rows),
            min_rows=min_rows,
            message="Veri yeterli; lightgbm paketi kurulunca eğitim başlatılabilir.",
        )

    split_at = max(1, int(len(rows) * 0.8))
    train_rows = rows[:split_at]
    valid_rows = rows[split_at:] or rows[-1:]
    train_x, train_y = _matrix(train_rows)
    valid_x, valid_y = _matrix(valid_rows)

    train_set = lgb.Dataset(train_x, label=train_y, feature_name=list(FEATURE_COLUMNS))
    valid_set = lgb.Dataset(valid_x, label=valid_y, reference=train_set)
    booster = lgb.train(
        {
            "objective": "binary",
            "metric": "binary_logloss",
            "verbosity": -1,
            "seed": 42,
        },
        train_set,
        valid_sets=[valid_set],
        num_boost_round=num_boost_round,
    )

    target_path = Path(model_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(target_path))
    latest_x, _ = _matrix([rows[-1]])
    probability = float(booster.predict(latest_x)[0])
    return MLTrainingResult(
        status="trained",
        rows=len(rows),
        min_rows=min_rows,
        message="LightGBM modeli eğitildi.",
        model_path=str(target_path),
        latest_probability=round(probability, 6),
    )


def predict_latest_probability(
    bars: list[dict[str, Any]],
    model_path: str | Path,
) -> float | None:
    """Eğitilmiş model varsa son bar için yükseliş olasılığı döndür."""
    target_path = Path(model_path)
    if not target_path.exists():
        return None
    rows = feature_rows_from_bars(bars)
    if not rows:
        return None
    try:
        import lightgbm as lgb
    except Exception:
        return None
    booster = lgb.Booster(model_file=str(target_path))
    latest_x, _ = _matrix([rows[-1]])
    return float(booster.predict(latest_x)[0])

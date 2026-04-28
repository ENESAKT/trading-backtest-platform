"""Strateji blueprint'leri — Sprint 3.3.

API tüketicisinin (frontend) gerek duyduğu meta:

* ``id``  — backend ``StrategyRegistry`` ismiyle aynı anahtar.
* ``label`` / ``description`` — TR görünüm metni.
* ``schema`` — UI form alanlarını üretmek için tip + sınır + varsayılan.

Yeni bir strateji eklemek için:

1. ``quant_engine/strategy/examples/`` altında ``BaseStrategy`` alt sınıfı yaz
   (``@register_strategy`` decorator'ı registry'ye otomatik kaydeder).
2. Bu modülde import et (decorator'ı tetiklesin) ve ``BLUEPRINTS``
   sözlüğüne meta + schema gir.
3. Mevcut 8 strateji listesi tamamlandığında Sprint 3.7 kapanır.
"""

from __future__ import annotations

from typing import Any

# `register_strategy` decorator'ı bu import'larla birlikte global registry'ye
# yazar — examples/__init__.py boş olduğu için explicit import zorunlu.
from quant_engine.strategy.examples.bollinger_reversion import (  # noqa: F401
    BollingerReversion,
)
from quant_engine.strategy.examples.buy_and_hold import BuyAndHold  # noqa: F401
from quant_engine.strategy.examples.rsi_reversion import RsiReversion  # noqa: F401
from quant_engine.strategy.examples.sma_crossover import SmaCrossover  # noqa: F401


_INT = "int"
_FLOAT = "float"


def _f(key: str, label: str, default: Any, type_: str = _INT,
       min_: float | None = None, max_: float | None = None,
       step: float | None = None, help_: str = "") -> dict[str, Any]:
    field: dict[str, Any] = {
        "key": key,
        "label": label,
        "type": type_,
        "default": default,
    }
    if min_ is not None:
        field["min"] = min_
    if max_ is not None:
        field["max"] = max_
    if step is not None:
        field["step"] = step
    if help_:
        field["help"] = help_
    return field


BLUEPRINTS: dict[str, dict[str, Any]] = {
    "sma_crossover": {
        "id": "sma_crossover",
        "label": "SMA Crossover",
        "description": "Çift hareketli ortalama kesişimi (Golden/Death Cross).",
        "default_params": {"fast_period": 10, "slow_period": 30},
        "schema": [
            _f("fast_period", "Hızlı SMA periyodu", 10,
               min_=2, max_=100, help_="Daha küçük → daha duyarlı"),
            _f("slow_period", "Yavaş SMA periyodu", 30,
               min_=5, max_=300, help_="Trend filtresi"),
        ],
    },
    "rsi_reversion": {
        "id": "rsi_reversion",
        "label": "RSI Mean-Reversion",
        "description": "Aşırı satım/aşırı alım bölgelerinden ortalamaya dönüş.",
        "default_params": {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
        },
        "schema": [
            _f("rsi_period", "RSI periyodu", 14, min_=2, max_=100),
            _f("oversold", "Aşırı satım eşiği", 30, min_=1, max_=49),
            _f("overbought", "Aşırı alım eşiği", 70, min_=51, max_=99),
        ],
    },
    "bollinger_reversion": {
        "id": "bollinger_reversion",
        "label": "Bollinger Bands Reversion",
        "description": "Bant dışına taşan fiyatın orta banda dönüşü.",
        "default_params": {"period": 20, "std_dev": 2.0},
        "schema": [
            _f("period", "BB periyodu", 20, min_=5, max_=100),
            _f("std_dev", "Standart sapma çarpanı", 2.0,
               type_=_FLOAT, min_=0.5, max_=4.0, step=0.1),
        ],
    },
    "buy_and_hold": {
        "id": "buy_and_hold",
        "label": "Buy & Hold",
        "description": "İlk barda al, son barda sat — pasif kıyas.",
        "default_params": {},
        "schema": [],
    },
}


def list_blueprints() -> list[dict[str, Any]]:
    """API'nin ``GET /api/backtest/strategies`` cevabı için sıralı liste."""
    return [BLUEPRINTS[k] for k in BLUEPRINTS]

"""Strategy Pack import/export yardımcıları.

Paket formatı dosya sistemi zorunluluğu olmadan ``.piyasapilot-strategy.json``
içeriğini temsil eder. Bu modül kasıtlı olarak saf fonksiyonlar içerir; API,
CLI veya frontend bağlantısı ayrı katmanda yapılır.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from quant_engine.strategy.spec import FormulaError, validate_strategy_spec

PACK_FILENAME = ".piyasapilot-strategy.json"
PACK_VERSION = 1

_PACK_KEYS = (
    "version",
    "strategy_spec",
    "params",
    "indicator_set",
    "risk_settings",
    "description",
    "example_backtest_metadata",
)


def export_strategy_pack(
    strategy_spec: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
    indicator_set: dict[str, Any] | list[Any] | None = None,
    risk_settings: dict[str, Any] | None = None,
    description: str = "",
    example_backtest_metadata: dict[str, Any] | None = None,
    version: int = PACK_VERSION,
    as_json: bool = False,
) -> dict[str, Any] | str:
    """Validate edilmiş Strategy Pack üret.

    ``as_json=True`` verildiğinde paket, deterministik JSON string olarak döner.
    Aksi halde JSON-serializable dict döndürülür.
    """

    if version in (None, ""):
        raise ValueError("Strategy Pack version alanı zorunludur")

    normalized_spec = _validate_strategy_spec(strategy_spec)
    pack = {
        "version": version,
        "strategy_spec": normalized_spec,
        "params": _copy_jsonable(params or {}, "params"),
        "indicator_set": _copy_jsonable(indicator_set or {}, "indicator_set"),
        "risk_settings": _copy_jsonable(risk_settings or {}, "risk_settings"),
        "description": str(description or ""),
        "example_backtest_metadata": _copy_jsonable(
            example_backtest_metadata or {},
            "example_backtest_metadata",
        ),
    }
    _assert_json_serializable(pack)
    if as_json:
        return json.dumps(pack, ensure_ascii=False, sort_keys=True)
    return pack


def import_strategy_pack(raw: dict[str, Any] | str | bytes) -> dict[str, Any]:
    """Strategy Pack dict/JSON içeriğini doğrula ve normalize edilmiş dict döndür."""

    pack = _coerce_pack(raw)
    missing = [key for key in _PACK_KEYS if key not in pack]
    if missing:
        raise ValueError(f"Eksik Strategy Pack alanları: {', '.join(missing)}")
    if pack["version"] in (None, ""):
        raise ValueError("Strategy Pack version alanı zorunludur")

    normalized_spec = _validate_strategy_spec(pack["strategy_spec"])
    normalized = {
        "version": pack["version"],
        "strategy_spec": normalized_spec,
        "params": _require_mapping(pack["params"], "params"),
        "indicator_set": _require_jsonable_collection(
            pack["indicator_set"],
            "indicator_set",
        ),
        "risk_settings": _require_mapping(pack["risk_settings"], "risk_settings"),
        "description": str(pack["description"] or ""),
        "example_backtest_metadata": _require_mapping(
            pack["example_backtest_metadata"],
            "example_backtest_metadata",
        ),
    }
    _assert_json_serializable(normalized)
    return normalized


def export_strategy_pack_json(strategy_spec: dict[str, Any], **kwargs: Any) -> str:
    """JSON string isteyen çağrılar için küçük kolaylık sarmalayıcısı."""

    out = export_strategy_pack(strategy_spec, as_json=True, **kwargs)
    return str(out)


def _coerce_pack(raw: dict[str, Any] | str | bytes) -> dict[str, Any]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Strategy Pack JSON okunamadı: {exc.msg}") from exc
        raw = loaded
    if not isinstance(raw, dict):
        raise ValueError("Strategy Pack kök değeri JSON nesnesi olmalıdır")
    return deepcopy(raw)


def _validate_strategy_spec(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("strategy_spec alanı nesne olmalıdır")
    try:
        return validate_strategy_spec(value)
    except FormulaError as exc:
        raise ValueError(f"Geçersiz strategy_spec: {exc}") from exc


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} alanı nesne olmalıdır")
    return _copy_jsonable(value, field)


def _require_jsonable_collection(value: Any, field: str) -> dict[str, Any] | list[Any]:
    if not isinstance(value, (dict, list)):
        raise ValueError(f"{field} alanı nesne veya liste olmalıdır")
    return _copy_jsonable(value, field)


def _copy_jsonable(value: Any, field: str) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False))
    except TypeError as exc:
        raise ValueError(f"{field} alanı JSON serializable olmalıdır") from exc


def _assert_json_serializable(value: Any) -> None:
    try:
        json.dumps(value, ensure_ascii=False)
    except TypeError as exc:
        raise ValueError("Strategy Pack JSON serializable olmalıdır") from exc

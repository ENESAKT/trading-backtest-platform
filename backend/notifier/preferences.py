"""Telegram notification preferences.

Preferences are intentionally stored outside secrets. They control what the
notifier sends, while token/chat credentials stay in environment variables.
"""

from __future__ import annotations

import json
import datetime as dt
from typing import Any

from backend.config import ROOT, getenv
from backend.data.symbols import BIST_STOCKS, CRYPTO_WS_SYMBOLS

PREFERENCES_PATH = ROOT / "data" / "runtime" / "telegram_preferences.json"

BIST100_EXTRA: tuple[str, ...] = (
    "AEFES.IS", "AGHOL.IS", "AKCNS.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS",
    "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ASTOR.IS",
    "ASUZU.IS", "AYGAZ.IS", "BAGFS.IS", "BERA.IS", "BIENY.IS", "BRISA.IS",
    "BRSAN.IS", "BRYAT.IS", "CCOLA.IS", "CIMSA.IS", "CLEBI.IS", "DOAS.IS",
    "ECILC.IS", "EGEEN.IS", "ENJSA.IS", "GENIL.IS", "GOODY.IS", "GUBRF.IS",
    "GWIND.IS", "HEKTS.IS", "IPEKE.IS", "ISDMR.IS", "ISMEN.IS", "IZMDC.IS",
    "KAREL.IS", "KARSN.IS", "KCAER.IS", "KMPUR.IS", "KONTR.IS", "KORDS.IS",
    "KOZAA.IS", "LOGO.IS", "MGROS.IS", "MPARK.IS", "NETAS.IS", "NUHCM.IS",
    "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PAPIL.IS", "POLHO.IS", "SDTTR.IS",
    "SELEC.IS", "SKBNK.IS", "SMRTG.IS", "SOKM.IS", "TKFEN.IS", "TSKB.IS",
    "TTRAK.IS", "TUKAS.IS", "TURSG.IS", "ULKER.IS", "YATAS.IS", "YEOTK.IS",
    "ZOREN.IS",
)

SYMBOL_GROUPS: dict[str, tuple[str, ...]] = {
    "bist30": BIST_STOCKS,
    "bist100": (*BIST_STOCKS, *BIST100_EXTRA),
    "crypto": CRYPTO_WS_SYMBOLS,
    "custom": (),
}

DEFAULT_PREFERENCES: dict[str, Any] = {
    "enabled": False,
    "notify_signals": True,
    "notify_trades": False,
    "notify_system": False,
    "notify_daily_summary": True,
    "symbol_group": "crypto",
    "custom_symbols": [],
    "signal_types": ["STRONG_BUY", "STRONG_SELL"],
    "min_strength": 8,
    "min_consensus_ratio": 0.6,
    "cooldown_minutes": 30,
    "quiet_hours": "",
    "consent_accepted": False,
    "consent_version": "",
    "consent_accepted_at": "",
    "consent_text": "",
}


def _split_csv(value: str) -> list[str]:
    return [part.strip().upper() for part in value.split(",") if part.strip()]


def _env_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    signal_types = getenv("TELEGRAM_SIGNAL_TYPES")
    symbols = getenv("TELEGRAM_SYMBOLS")
    if signal_types:
        overrides["signal_types"] = _split_csv(signal_types)
    if symbols:
        overrides["symbol_group"] = "custom"
        overrides["custom_symbols"] = _split_csv(symbols)
    for key, env_name in (
        ("min_strength", "TELEGRAM_MIN_STRENGTH"),
        ("cooldown_minutes", "TELEGRAM_COOLDOWN_MINUTES"),
    ):
        raw = getenv(env_name)
        if raw:
            try:
                overrides[key] = int(raw)
            except ValueError:
                pass
    raw_ratio = getenv("TELEGRAM_MIN_CONSENSUS_RATIO")
    if raw_ratio:
        try:
            overrides["min_consensus_ratio"] = float(raw_ratio)
        except ValueError:
            pass
    quiet = getenv("TELEGRAM_QUIET_HOURS")
    if quiet:
        overrides["quiet_hours"] = quiet
    return overrides


def _normalize_symbols(symbols: Any) -> list[str]:
    if isinstance(symbols, str):
        raw = _split_csv(symbols)
    elif isinstance(symbols, list):
        raw = [str(item).strip().upper() for item in symbols if str(item).strip()]
    else:
        raw = []
    seen: set[str] = set()
    result: list[str] = []
    for symbol in raw:
        if symbol not in seen:
            seen.add(symbol)
            result.append(symbol)
    return result[:200]


def normalize_preferences(raw: dict[str, Any] | None) -> dict[str, Any]:
    prefs = dict(DEFAULT_PREFERENCES)
    if raw:
        prefs.update(raw)

    prefs["enabled"] = bool(prefs.get("enabled"))
    prefs["consent_accepted"] = bool(prefs.get("consent_accepted"))
    if prefs["enabled"] and not prefs["consent_accepted"]:
        prefs["enabled"] = False
    prefs["notify_signals"] = bool(prefs.get("notify_signals"))
    prefs["notify_trades"] = bool(prefs.get("notify_trades"))
    prefs["notify_system"] = bool(prefs.get("notify_system"))
    prefs["notify_daily_summary"] = bool(prefs.get("notify_daily_summary"))

    group = str(prefs.get("symbol_group") or "crypto").lower()
    prefs["symbol_group"] = group if group in SYMBOL_GROUPS else "custom"
    prefs["custom_symbols"] = _normalize_symbols(prefs.get("custom_symbols"))

    signal_types = _normalize_symbols(prefs.get("signal_types"))
    allowed_types = {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}
    prefs["signal_types"] = [t for t in signal_types if t in allowed_types] or [
        "STRONG_BUY",
        "STRONG_SELL",
    ]

    prefs["min_strength"] = max(1, min(10, int(prefs.get("min_strength") or 1)))
    prefs["cooldown_minutes"] = max(0, min(1440, int(prefs.get("cooldown_minutes") or 0)))
    prefs["min_consensus_ratio"] = max(
        0.0, min(1.0, float(prefs.get("min_consensus_ratio") or 0.0))
    )
    prefs["quiet_hours"] = str(prefs.get("quiet_hours") or "").strip()
    prefs["consent_version"] = str(prefs.get("consent_version") or "").strip()
    prefs["consent_accepted_at"] = str(prefs.get("consent_accepted_at") or "").strip()
    prefs["consent_text"] = str(prefs.get("consent_text") or "").strip()
    return prefs


def read_preferences() -> dict[str, Any]:
    data: dict[str, Any] = {}
    try:
        if PREFERENCES_PATH.exists():
            data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    prefs = normalize_preferences(data)
    prefs.update(_env_overrides())
    return normalize_preferences(prefs)


def write_preferences(raw: dict[str, Any]) -> dict[str, Any]:
    prefs = normalize_preferences(raw)
    if prefs["consent_accepted"] and not prefs["consent_accepted_at"]:
        prefs["consent_accepted_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    if prefs["consent_accepted"] and not prefs["consent_version"]:
        prefs["consent_version"] = "2026-05-23"
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PREFERENCES_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PREFERENCES_PATH)
    return prefs


def selected_symbols(prefs: dict[str, Any] | None = None) -> list[str]:
    current = prefs or read_preferences()
    group = str(current.get("symbol_group") or "custom").lower()
    if group == "custom":
        return list(current.get("custom_symbols") or [])
    return list(SYMBOL_GROUPS.get(group, ()))


def public_preferences() -> dict[str, Any]:
    prefs = read_preferences()
    return {
        **prefs,
        "selected_symbols": selected_symbols(prefs),
        "available_groups": {
            "bist30": len(SYMBOL_GROUPS["bist30"]),
            "bist100": len(SYMBOL_GROUPS["bist100"]),
            "crypto": len(SYMBOL_GROUPS["crypto"]),
            "custom": len(prefs.get("custom_symbols") or []),
        },
    }

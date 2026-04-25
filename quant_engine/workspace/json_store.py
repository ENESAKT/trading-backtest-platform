"""
Workspace JSON store for the Data Station.

Kullanıcının eklediği veri kaynakları, sembol grupları ve veri setleri tek bir
JSON sözleşmesinde tutulur. Yazma işlemi atomic yapılır; bozuk dosya yüzünden
terminalin açılmaması yerine doğrulanmış varsayılan belgeye dönülür.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_WORKSPACE_JSON_PATH = Path("data/workspaces/workspace.json")


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def default_workspace_document() -> dict[str, Any]:
    now = _utc_now_iso()
    return {
        "schema_version": 1,
        "updated_at": now,
        "api_sources": [
            {
                "name": "Yahoo Finance",
                "provider": "yfinance",
                "base_url": "https://query1.finance.yahoo.com",
                "auth_type": "none",
                "enabled": True,
                "notes": "BIST, döviz ve emtia için gün sonu/limitli intraday gerçek veri.",
                "created_at": now,
            },
            {
                "name": "Binance Spot",
                "provider": "binance",
                "base_url": "https://data-api.binance.vision",
                "auth_type": "none",
                "enabled": True,
                "notes": "Kripto liderleri için public kline/OHLCV gerçek veri.",
                "created_at": now,
            },
        ],
        "symbol_groups": [
            {
                "name": "Piyasa Özeti",
                "market": "mixed",
                "symbols": ["XU100", "USDTRY", "XAUUSD", "BTCUSDT", "ETHUSDT"],
                "created_at": now,
            }
        ],
        "datasets": [],
    }


def validate_workspace_document(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["schema_version", "api_sources", "symbol_groups", "datasets"]:
        if key not in document:
            errors.append(f"Eksik anahtar: {key}")
    if not isinstance(document.get("api_sources", []), list):
        errors.append("api_sources liste olmalı")
    if not isinstance(document.get("symbol_groups", []), list):
        errors.append("symbol_groups liste olmalı")
    if not isinstance(document.get("datasets", []), list):
        errors.append("datasets liste olmalı")
    return errors


class WorkspaceJsonStore:
    """Atomic JSON-backed configuration store."""

    def __init__(self, path: str | Path = DEFAULT_WORKSPACE_JSON_PATH):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            document = default_workspace_document()
            self.save(document)
            return document
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            document = default_workspace_document()
            self.save(document)
            return document
        errors = validate_workspace_document(document)
        if errors:
            document = default_workspace_document()
            document["warnings"] = errors
            self.save(document)
        return document

    def save(self, document: dict[str, Any]) -> None:
        document = dict(document)
        document["updated_at"] = _utc_now_iso()
        errors = validate_workspace_document(document)
        if errors:
            raise ValueError("; ".join(errors))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            dir=str(self.path.parent),
        )
        try:
            os.close(tmp_fd)
            Path(tmp_path).write_text(f"{payload}\n", encoding="utf-8")
            Path(tmp_path).replace(self.path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def upsert_api_source(
        self,
        *,
        name: str,
        provider: str,
        base_url: str,
        auth_type: str = "none",
        enabled: bool = True,
        notes: str = "",
    ) -> dict[str, Any]:
        document = self.load()
        sources = [
            source
            for source in document["api_sources"]
            if source.get("name", "").lower() != name.lower()
        ]
        sources.append(
            {
                "name": name.strip(),
                "provider": provider.strip(),
                "base_url": base_url.strip(),
                "auth_type": auth_type,
                "enabled": bool(enabled),
                "notes": notes.strip(),
                "created_at": _utc_now_iso(),
            }
        )
        document["api_sources"] = sources
        self.save(document)
        return document

    def upsert_symbol_group(
        self,
        *,
        name: str,
        market: str,
        symbols: list[str],
    ) -> dict[str, Any]:
        clean_symbols = [item.upper().strip() for item in symbols if item.strip()]
        if not clean_symbols:
            raise ValueError("Sembol grubu en az bir sembol içermeli.")
        document = self.load()
        groups = [
            group
            for group in document["symbol_groups"]
            if group.get("name", "").lower() != name.lower()
        ]
        groups.append(
            {
                "name": name.strip(),
                "market": market.strip(),
                "symbols": list(dict.fromkeys(clean_symbols)),
                "created_at": _utc_now_iso(),
            }
        )
        document["symbol_groups"] = groups
        self.save(document)
        return document

    def upsert_dataset(
        self,
        *,
        name: str,
        source: str,
        market: str,
        timeframe: str,
        layer: str,
        symbols: list[str],
    ) -> dict[str, Any]:
        clean_symbols = [item.upper().strip() for item in symbols if item.strip()]
        if not clean_symbols:
            raise ValueError("Veri seti en az bir sembol içermeli.")
        document = self.load()
        datasets = [
            dataset
            for dataset in document["datasets"]
            if dataset.get("name", "").lower() != name.lower()
        ]
        datasets.append(
            {
                "name": name.strip(),
                "source": source.strip(),
                "market": market.strip(),
                "timeframe": timeframe.strip(),
                "layer": layer.strip(),
                "symbols": list(dict.fromkeys(clean_symbols)),
                "created_at": _utc_now_iso(),
            }
        )
        document["datasets"] = datasets
        self.save(document)
        return document

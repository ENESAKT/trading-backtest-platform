"""Telegram listener durumunu süreçler arasında güvenli paylaş."""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

from backend.config import ROOT, mask_sensitive

STATUS_PATH = ROOT / "data" / "runtime" / "telegram_listener_status.json"
STALE_SECONDS = 90


def utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def write_listener_status(status: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    safe = {
        "aktif": bool(status.get("aktif", False)),
        "islenen_mesaj": int(status.get("islenen_mesaj", 0) or 0),
        "son_mesaj": mask_sensitive(status.get("son_mesaj")),
        "son_hata": mask_sensitive(status.get("son_hata")),
        "updated_at": utc_iso(),
    }
    tmp = STATUS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(safe, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATUS_PATH)


def read_listener_status() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    updated_at = data.get("updated_at")
    active = bool(data.get("aktif", False))
    if updated_at:
        try:
            ts = dt.datetime.fromisoformat(updated_at)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.UTC)
            age = (dt.datetime.now(dt.UTC) - ts.astimezone(dt.UTC)).total_seconds()
            if age > STALE_SECONDS:
                active = False
        except Exception:  # noqa: BLE001
            active = False

    data["aktif"] = active
    return data

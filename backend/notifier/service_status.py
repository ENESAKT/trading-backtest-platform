"""Notifier servis durumunu süreçler arasında güvenli paylaş."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from backend.config import ROOT, mask_sensitive

STATUS_PATH = ROOT / "data" / "runtime" / "notifier_status.json"
STALE_SECONDS = 90


def _utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def write_notifier_status(status: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    safe = {
        "aktif": bool(status.get("aktif", False)),
        "son_bildirim": status.get("son_bildirim"),
        "son_hata": mask_sensitive(status.get("son_hata")),
        "toplam_bildirim": int(status.get("toplam_bildirim", 0) or 0),
        "updated_at": _utc_iso(),
    }
    tmp = STATUS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(safe, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATUS_PATH)


def read_notifier_status() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    active = bool(data.get("aktif", False))
    updated_at = data.get("updated_at")
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

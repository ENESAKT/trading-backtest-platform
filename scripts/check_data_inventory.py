#!/usr/bin/env python3
"""Veri envanteri sema ve dokumantasyon hizasi kontrolu."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        ROOT / "infra" / "clickhouse" / "init" / "001_market_bars.sql",
        ROOT / "infra" / "clickhouse" / "init" / "002_quality_events.sql",
        ROOT / "infra" / "mysql" / "migrations" / "003_inventory.sql",
        ROOT / "backend" / "data" / "repositories" / "market_data_facade.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        print("FAIL eksik veri platform dosyasi: " + ", ".join(missing))
        return 1
    facade = (ROOT / "backend" / "data" / "repositories" / "market_data_facade.py").read_text(encoding="utf-8")
    for token in ("clickhouse", "redis"):
        if token not in facade:
            print(f"FAIL facade source token eksik: {token}")
            return 1
    print("OK data inventory: schemas and facade source contract present")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Retention sema ve guvenli cleanup kontrati kontrolu."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    retention_sql = ROOT / "infra" / "mysql" / "migrations" / "004_retention.sql"
    cleanup = ROOT / "backend" / "data" / "ingest" / "retention.py"
    if not retention_sql.exists() or not cleanup.exists():
        print("FAIL retention migration veya cleanup modulu eksik")
        return 1
    sql = retention_sql.read_text(encoding="utf-8").lower()
    code = cleanup.read_text(encoding="utf-8").lower()
    if "retention" not in sql:
        print("FAIL retention migration retention kontrati icermiyor")
        return 1
    if "delete" not in code and "ttl" not in code:
        print("FAIL cleanup modulu silme/ttl uygulama kontrati icermiyor")
        return 1
    print("OK retention: migration and cleanup contract present")
    return 0

if __name__ == "__main__":
    sys.exit(main())

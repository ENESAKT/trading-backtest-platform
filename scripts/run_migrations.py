#!/usr/bin/env python3
"""Apply MySQL migrations in infra/mysql/migrations once."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

import pymysql

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "infra" / "mysql" / "migrations"


def connect():
    raw = os.environ.get("DATABASE_URL", "")
    parsed = urlparse(raw) if raw else None
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST") or (parsed.hostname if parsed else None) or "localhost",
        port=int(os.environ.get("MYSQL_PORT") or (parsed.port if parsed else 3306)),
        user=os.environ.get("MYSQL_USER") or (parsed.username if parsed else None) or "piyasapilot",
        password=os.environ.get("MYSQL_PASSWORD") or (parsed.password if parsed else None) or "piyasapilot",
        database=os.environ.get("MYSQL_DATABASE") or ((parsed.path or "").lstrip("/") if parsed else "") or "piyasapilot",
        charset="utf8mb4",
        autocommit=False,
    )


def split_sql(sql: str) -> list[str]:
    statements: list[str] = []
    buff: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buff.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buff).rstrip(";"))
            buff = []
    if buff:
        statements.append("\n".join(buff))
    return statements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = sorted(MIGRATIONS.glob("*.sql"))
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            conn.commit()
            for path in files:
                version = path.name
                cur.execute("SELECT version FROM schema_migrations WHERE version=%s", (version,))
                if cur.fetchone():
                    print(f"SKIP {version}")
                    continue
                print(f"APPLY {version}")
                if args.dry_run:
                    continue
                for statement in split_sql(path.read_text(encoding="utf-8")):
                    cur.execute(statement)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
                conn.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

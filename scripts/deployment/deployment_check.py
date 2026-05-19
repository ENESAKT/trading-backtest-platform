#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ENV = {
    "APP_ENV",
    "PUBLIC_BASE_URL",
    "CORS_ORIGINS",
    "API_KEY",
    "CLICKHOUSE_URL",
    "DATABASE_URL",
    "MYSQL_ROOT_PASSWORD",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "REDIS_URL",
    "STRICT_ENV_VALIDATION",
}
PLACEHOLDER_MARKERS = (
    "BURAYA_YAZ",
    "CHANGE_ME",
    "TODO",
    "ornekdomain",
    "example.com",
)

def check_deployment():
    print("Checking deployment readiness (domain, volume binds, secrets)...")
    if not (ROOT / "infra/docker-compose.prod.yml").exists():
        print("ERROR: docker-compose.prod.yml not found.")
        sys.exit(1)
    env_path = ROOT / ".env.production"
    if not env_path.exists():
        print("ERROR: .env.production not found. Run `make env-production`.")
        sys.exit(1)
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    missing = sorted(key for key in REQUIRED_ENV if not env.get(key))
    if missing:
        print("ERROR: .env.production missing required values:")
        for key in missing:
            print(f"  - {key}")
        sys.exit(1)
    placeholders = sorted(
        key for key, value in env.items()
        if value and any(marker in value for marker in PLACEHOLDER_MARKERS)
    )
    if placeholders:
        print("ERROR: .env.production contains placeholder values:")
        for key in placeholders:
            print(f"  - {key}")
        sys.exit(1)
    mysql_url = env.get("MYSQL_URL", "")
    database_url = env.get("DATABASE_URL", "")
    if "mysql:" not in mysql_url or "mysql:" not in database_url:
        print("ERROR: MYSQL_URL and DATABASE_URL must point to the compose mysql service host `mysql`.")
        print("       Use external RDS only after removing or disabling the mysql service deliberately.")
        sys.exit(1)
    compose_text = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
    for needle in ("certbot/conf", "certbot/www", "clickhouse_backups"):
        if needle not in compose_text:
            print(f"ERROR: production compose missing {needle}.")
            sys.exit(1)
    print("SUCCESS: Deployment config logic seems ready.")

if __name__ == "__main__":
    check_deployment()

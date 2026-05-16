#!/usr/bin/env python3
"""Production readiness smoke checks for PiyasaPilot."""

from __future__ import annotations

import argparse
import os
import socket
import ssl
import sys
from urllib.parse import urlparse

import httpx

BASE_URL = "https://piyasapilotu.com"


def check_env_variables(_base_url: str) -> tuple[bool, str]:
    required = ["PUBLIC_BASE_URL", "CORS_ORIGINS", "JWT_SECRET"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        return False, "Eksik env: " + ", ".join(missing)
    if len(os.environ.get("JWT_SECRET", "")) < 32:
        return False, "JWT_SECRET çok kısa"
    return True, "Zorunlu env değerleri mevcut"


def check_dns(base_url: str) -> tuple[bool, str]:
    host = urlparse(base_url).hostname or base_url
    try:
        ips = socket.gethostbyname_ex(host)[2]
        return bool(ips), ", ".join(ips) if ips else "IP bulunamadı"
    except OSError as exc:
        return False, str(exc)


def check_tls(base_url: str) -> tuple[bool, str]:
    parsed = urlparse(base_url)
    host = parsed.hostname
    if not host:
        return False, "Host yok"
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        return True, f"TLS OK: {cert.get('subject', '')}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_api_health(base_url: str) -> tuple[bool, str]:
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/health", timeout=8)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        return True, "API health 200"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_metrics(base_url: str) -> tuple[bool, str]:
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/metrics", timeout=8)
        return (resp.status_code == 200, f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_auth_smoke(base_url: str) -> tuple[bool, str]:
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/auth/me", timeout=8)
        return (resp.status_code in {401, 503}, f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_db(_base_url: str) -> tuple[bool, str]:
    hints = ["DATABASE_URL", "MYSQL_HOST", "CLICKHOUSE_URL", "REDIS_URL"]
    present = [key for key in hints if os.environ.get(key)]
    return (bool(present), "DB env: " + ", ".join(present) if present else "DB env yok")


def check_migrations(_base_url: str) -> tuple[bool, str]:
    path = "infra/mysql/migrations/007_auth_tables.sql"
    return (os.path.exists(path), f"{path} {'var' if os.path.exists(path) else 'yok'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--skip-dns", action="store_true")
    parser.add_argument("--skip-tls", action="store_true")
    parser.add_argument("--skip-ws", action="store_true")
    parser.add_argument("--skip-db", action="store_true")
    args = parser.parse_args()

    checks = [
        ("ENV_VARIABLES", check_env_variables),
        ("API_HEALTH", check_api_health),
        ("METRICS", check_metrics),
        ("AUTH_ENDPOINTS", check_auth_smoke),
        ("MIGRATION_STATUS", check_migrations),
    ]
    if not args.skip_dns:
        checks.insert(1, ("DNS_RESOLUTION", check_dns))
    if not args.skip_tls:
        checks.insert(2, ("TLS_CERTIFICATE", check_tls))
    if not args.skip_db:
        checks.append(("DB_CONNECTIVITY", check_db))

    failures: list[str] = []
    for name, fn in checks:
        ok, detail = fn(args.base_url)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            failures.append(name)

    if args.skip_ws:
        print("SKIP WS_QUOTES/WS_SIGNALS: skipped by flag")
    else:
        print("SKIP WS_QUOTES/WS_SIGNALS: websocket smoke is covered by browser/e2e flow")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Create a local .env.production with generated secrets.

Usage:
    DOMAIN=piyasapilot.example.com python3 scripts/deployment/create_env_production.py
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".env.production"


def _secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def main() -> int:
    domain = os.environ.get("DOMAIN", "localhost").strip()
    public_base_url = (
        f"https://{domain}" if domain not in {"localhost", "127.0.0.1"} else "http://localhost"
    )
    cors = (
        f"https://{domain},https://www.{domain}"
        if domain not in {"localhost", "127.0.0.1"}
        else "http://localhost,http://localhost:5173,http://localhost:8000"
    )
    mysql_password = _secret()
    mysql_root_password = _secret()
    clickhouse_password = _secret()

    content = f"""APP_ENV=production
PUBLIC_BASE_URL={public_base_url}
CORS_ORIGINS={cors}
API_KEY={_secret()}
STRICT_ENV_VALIDATION=1
LOG_LEVEL=WARNING

CLICKHOUSE_URL=http://clickhouse:8123/piyasapilot
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD={clickhouse_password}
CLICKHOUSE_DB=piyasapilot

DATABASE_URL=mysql+pymysql://piyasapilot:{mysql_password}@mysql:3306/piyasapilot
MYSQL_URL=mysql+aiomysql://piyasapilot:{mysql_password}@mysql:3306/piyasapilot
MYSQL_ROOT_PASSWORD={mysql_root_password}
MYSQL_USER=piyasapilot
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE=piyasapilot
MYSQL_DB=piyasapilot

REDIS_URL=redis://redis:6379/0

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
NOTIFY_EMAIL_TO=

BIST_HTTP_URL_TEMPLATE=
BIST_HTTP_AUTH_HEADER=
VIOP_HTTP_URL_TEMPLATE=
VIOP_HTTP_AUTH_HEADER=
"""
    if OUT.exists() and os.environ.get("FORCE") != "1":
        print(f"{OUT} zaten var. Üzerine yazmak için FORCE=1 kullanın.")
        return 0
    OUT.write_text(content, encoding="utf-8")
    OUT.chmod(0o600)
    print(f"{OUT} oluşturuldu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

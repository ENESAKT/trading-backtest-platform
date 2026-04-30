"""Telegram `/kontrol` komutu için güvenli doğrulama.

Varsayılan mod handler'ı kuru çalıştırır. `--live` verilirse Telegram API'ye
getMe çağrısı yapar; token/chat id yazdırmaz.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

async def _live_check() -> bool:
    from backend.config import getenv, telegram_configured

    if not telegram_configured():
        print("telegram_live=false reason=not_configured")
        return False
    import httpx

    token = getenv("TELEGRAM_BOT_TOKEN")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
    ok = resp.status_code == 200 and bool(resp.json().get("ok"))
    print(f"telegram_live={str(ok).lower()}")
    return ok


async def _dry_check() -> bool:
    from backend.notifier.telegram_commands import cmd_kontrol

    text = await cmd_kontrol("")
    ok = "PiyasaPilot" in text or "Sağlık" in text or "kontrol" in text.lower()
    print(f"telegram_kontrol_handler={str(ok).lower()}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    ok = asyncio.run(_live_check() if args.live else _dry_check())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

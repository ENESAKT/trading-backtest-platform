#!/usr/bin/env python3
"""Günlük sağlık raporu — /api/health çek, Telegram'a gönder.

Kullanım:
    python scripts/daily_health_report.py [--url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def fetch_health(base_url: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def build_message(health: dict) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if health.get("status") == "error":
        return f"[{now}] PiyasaPilot SAĞLIK HATASI: {health.get('error', 'bilinmiyor')}"

    cache = health.get("cache", {})
    bars = cache.get("rows", 0)
    symbols = cache.get("distinct_symbols", 0)
    workers = health.get("workers", [])
    up_count = sum(1 for w in workers if w.get("running"))
    total = len(workers)

    lines = [
        f"PiyasaPilot Günlük Rapor — {now}",
        f"Cache: {bars:,} bar, {symbols} sembol",
        f"Worker: {up_count}/{total} aktif",
    ]

    for w in workers:
        name = w.get("name", "?")
        status = "✅" if w.get("running") else "❌"
        iters = w.get("iterations", 0)
        lines.append(f"  {status} {name}: {iters} iter")

    sig_bus = health.get("signal_bus", {})
    subs = sig_bus.get("subscribers", 0)
    lines.append(f"Sinyal bus: {subs} abone")

    return "\n".join(lines)


def send_telegram(message: str) -> bool:
    try:
        from backend.config import getenv
        token = getenv("TELEGRAM_BOT_TOKEN")
        chat_id = getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            print("[Telegram] Yapılandırılmamış — mesaj sadece stdout'a yazılıyor.")
            return False

        payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"[Telegram] Gönderim hatası: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Günlük sağlık raporu")
    parser.add_argument("--url", default="http://localhost:8000", help="Gateway URL")
    parser.add_argument("--no-telegram", action="store_true", help="Sadece stdout")
    args = parser.parse_args()

    health = fetch_health(args.url)
    message = build_message(health)
    print(message)

    if not args.no_telegram:
        sent = send_telegram(message)
        if sent:
            print("[Telegram] Rapor gönderildi.")


if __name__ == "__main__":
    main()

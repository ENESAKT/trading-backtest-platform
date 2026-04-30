"""Çalışan backend'in `/metrics` çıktısını Prometheus formatında doğrula."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from backend.config import getenv

    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    headers = {}
    api_key = getenv("API_KEY")
    if api_key:
        headers["X-API-Key"] = api_key
    req = Request(f"{args.base_url.rstrip('/')}/metrics", headers=headers)
    with urlopen(req, timeout=10) as response:
        text = response.read().decode("utf-8")

    required = [
        "# HELP gateway_cache_bars_total",
        "gateway_cache_bars_total",
        "gateway_worker_up",
        "gateway_signal_bus_subscribers",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        print(f"metrics_ok=false missing={','.join(missing)}")
        return 1
    print("metrics_ok=true")
    print(text.strip().splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""PiyasaPilot canlı veri stres testi.

Varsayılan smoke modu kısa sürer. Rapordaki 100 sembol x 1 saat testi için:

    source .venv/bin/activate
    python scripts/stress_live_data.py --symbols 100 --duration-seconds 3600

Test backend'i başlatmaz; çalışan gateway'e HTTP üzerinden gider.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@dataclass
class StressResult:
    requests: int = 0
    ok: int = 0
    failed: int = 0
    provider_empty_or_error: int = 0
    max_latency_ms: float = 0.0


def symbol_pool(count: int) -> list[str]:
    from backend.data.symbols import BIST_STOCKS, CRYPTO_WS_SYMBOLS, YAHOO_INDEX_FX_COMMODITY

    base = [*BIST_STOCKS, *CRYPTO_WS_SYMBOLS, *YAHOO_INDEX_FX_COMMODITY]
    expanded: list[str] = []
    i = 0
    while len(expanded) < count:
        expanded.append(base[i % len(base)])
        i += 1
    return expanded[:count]


async def fetch_once(
    client: httpx.AsyncClient,
    base_url: str,
    symbol: str,
    result: StressResult,
) -> None:
    started = time.perf_counter()
    try:
        resp = await client.get(
            f"{base_url}/api/v2/candles",
            params={"symbol": symbol, "interval": "15m", "limit": 120},
        )
        result.requests += 1
        latency_ms = (time.perf_counter() - started) * 1000
        result.max_latency_ms = max(result.max_latency_ms, latency_ms)
        payload: dict[str, Any] = resp.json()
        if resp.status_code == 200 and payload.get("status") != "invalid":
            result.ok += 1
            if payload.get("status") in {"error", "no_data", "not_configured"}:
                result.provider_empty_or_error += 1
        else:
            result.failed += 1
    except Exception:
        result.requests += 1
        result.failed += 1


async def run(args: argparse.Namespace) -> StressResult:
    result = StressResult()
    symbols = symbol_pool(args.symbols)
    deadline = time.monotonic() + args.duration_seconds
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    async with httpx.AsyncClient(timeout=args.timeout, limits=limits) as client:
        while time.monotonic() < deadline:
            for start in range(0, len(symbols), args.concurrency):
                batch = symbols[start : start + args.concurrency]
                await asyncio.gather(
                    *(
                        fetch_once(client, args.base_url.rstrip("/"), symbol, result)
                        for symbol in batch
                    )
                )
                if time.monotonic() >= deadline:
                    break
            await asyncio.sleep(args.pause_seconds)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--symbols", type=int, default=100)
    parser.add_argument("--duration-seconds", type=int, default=60)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--pause-seconds", type=float, default=0.0)
    parser.add_argument("--max-fail-rate", type=float, default=0.02)
    args = parser.parse_args()

    result = asyncio.run(run(args))
    fail_rate = (result.failed / result.requests) if result.requests else 1.0
    print(
        f"requests={result.requests} ok={result.ok} failed={result.failed} "
        f"provider_empty_or_error={result.provider_empty_or_error} "
        f"fail_rate={fail_rate:.2%} max_latency_ms={result.max_latency_ms:.1f}"
    )
    return 0 if result.requests > 0 and fail_rate <= args.max_fail_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())

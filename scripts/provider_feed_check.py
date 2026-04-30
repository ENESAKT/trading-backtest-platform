"""Lisanslı BIST/VİOP feed köprülerini doğrula.

Varsayılan mod dış credential yoksa hata üretmez; durumu JSON olarak
``external_credential_missing`` döndürür. CI/kurulum anında gerçek zorunlu
kontrol için ``--require-config`` kullanılabilir. ``--mock`` modu yerel HTTP
feed başlatır ve adapter zincirini uçtan uca test eder.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _MockFeedHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        payload = {
            "bars": [
                {
                    "time": 1_700_000_000 + i * 900,
                    "open": 100 + i,
                    "high": 101 + i,
                    "low": 99 + i,
                    "close": 100.5 + i,
                    "volume": 1_000 + i,
                }
                for i in range(6)
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: Any) -> None:
        return


def _start_mock_feed() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockFeedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    template = f"http://127.0.0.1:{port}/{{symbol}}?tf={{timeframe}}&limit={{limit}}"
    os.environ["BIST_HTTP_URL_TEMPLATE"] = template
    os.environ["VIOP_HTTP_URL_TEMPLATE"] = template
    return server


def _check_result(
    name: str,
    env_name: str,
    symbol: str,
    provider: Any,
    timeframe: str,
    limit: int,
    require_config: bool,
) -> dict[str, Any]:
    from backend.config import getenv

    configured = bool(getenv(env_name))
    if not configured:
        return {
            "provider": name,
            "symbol": symbol,
            "configured": False,
            "status": "external_credential_missing",
            "ok": not require_config,
        }

    result = provider.fetch_ohlcv(symbol, timeframe, limit)
    ok = result.status.value == "ok" and result.is_real and bool(result.data)
    return {
        "provider": name,
        "symbol": result.symbol,
        "configured": True,
        "status": result.status.value,
        "is_real": result.is_real,
        "bars": len(result.data),
        "source": result.source,
        "ok": ok,
        "error": result.error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--bist-symbol", default="THYAO")
    parser.add_argument("--viop-symbol", default="F_XU0300426")
    parser.add_argument("--require-config", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    server: ThreadingHTTPServer | None = _start_mock_feed() if args.mock else None
    try:
        from quant_engine.data.providers.bist_provider import BistMarketDataProvider
        from quant_engine.data.providers.viop_provider import ViopMarketDataProvider

        checks = [
            _check_result(
                "bist",
                "BIST_HTTP_URL_TEMPLATE",
                args.bist_symbol,
                BistMarketDataProvider(),
                args.timeframe,
                args.limit,
                args.require_config,
            ),
            _check_result(
                "viop",
                "VIOP_HTTP_URL_TEMPLATE",
                args.viop_symbol,
                ViopMarketDataProvider(),
                args.timeframe,
                args.limit,
                args.require_config,
            ),
        ]
        report = {
            "status": "ok" if all(item["ok"] for item in checks) else "needs_attention",
            "mock": args.mock,
            "checks": checks,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if all(item["ok"] for item in checks) else 1
    finally:
        if server is not None:
            server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())

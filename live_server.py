"""
PiyasaPilot yerel canlı veri sunucusu.

Bu sunucu sadece public/read-only veri okur. API anahtarı kabul etmez, canlı emir
göndermez ve veri gelmediğinde sahte değer üretmez.

Çalıştırma:
    python3 live_server.py
    http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from quant_engine.data.live_feed import LiveDataService, PaperTradingRecorder
from quant_engine.workspace.json_store import WorkspaceJsonStore


ROOT = Path(__file__).resolve().parent


class PiyasaPilotHandler(SimpleHTTPRequestHandler):
    """Statik arayüzü ve JSON API endpointlerini sunar."""

    server_version = "PiyasaPilotLive/0.1"
    data_service = LiveDataService()
    paper_recorder = PaperTradingRecorder(data_service=data_service)
    workspace_store = WorkspaceJsonStore(ROOT / "data/workspaces/workspace.json")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(
                {
                    "status": "ok",
                    "read_only": True,
                    "message": "Canlı veri sunucusu çalışıyor. Emir motoru pasif.",
                }
            )
            return

        if parsed.path == "/api/market/defaults":
            self._send_json(self.data_service.fetch_default_dashboard())
            return

        if parsed.path == "/api/market/chart":
            params = parse_qs(parsed.query)
            symbol = (params.get("symbol") or [""])[0]
            limit = int((params.get("limit") or ["180"])[0])
            if not symbol:
                self._send_json({"status": "error", "message": "Sembol zorunludur."}, status=400)
                return
            self._send_json(self.data_service.fetch_chart(symbol, limit=limit))
            return

        if parsed.path == "/api/workspace":
            self._send_json(self.workspace_store.load())
            return

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/paper/signal":
            try:
                payload = self._read_json_body()
                trade = self.paper_recorder.record_signal(payload)
                self._send_json(
                    {
                        "status": "ok",
                        "message": "Sanal paper trade gerçek son fiyatla kaydedildi.",
                        "trade": trade,
                    }
                )
            except Exception as exc:
                self._send_json(
                    {
                        "status": "error",
                        "message": "Bağlantı Hatası",
                        "error": str(exc),
                    },
                    status=400,
                )
            return

        self._send_json({"status": "error", "message": "Endpoint bulunamadı."}, status=404)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw or "{}")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="PiyasaPilot canlı veri sunucusu")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), PiyasaPilotHandler)
    print(f"PiyasaPilot canlı veri sunucusu: http://{args.host}:{args.port}")
    print("Read-only mod aktif. Canlı emir motoru kapalı.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatıldı.")


if __name__ == "__main__":
    main()

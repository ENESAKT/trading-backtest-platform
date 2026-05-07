"""PiyasaPilot Gateway launcher.

Eski stdlib ``http.server`` tabanlı sunucu Sprint 1'de FastAPI/uvicorn'a terfi
etti. Bu dosya artık sadece ince bir CLI sarmalayıcı; gerçek uygulama
``backend.api.main:app`` içinde.

Çalıştırma:

    python3 live_server.py            # http://127.0.0.1:8000
    python3 live_server.py --reload   # geliştirme; auto-reload
    python3 live_server.py --port 8001

Read-only mod: API anahtarı kabul etmez, canlı emir göndermez.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PiyasaPilot v2 gateway (FastAPI + uvicorn)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload", action="store_true",
        help="Auto-reload on file changes (geliştirme).",
    )
    args = parser.parse_args()

    import uvicorn

    print(f"PiyasaPilot v2 gateway: http://{args.host}:{args.port}")
    print("Read-only mod aktif. Emir motoru kapalı.")

    uvicorn.run(
        "backend.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()

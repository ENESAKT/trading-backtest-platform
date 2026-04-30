"""MCP konfigürasyonu için hızlı, güvenli smoke kontrolü.

Bu script MCP sunucularını uzun süre açık tutmaz; yalnızca komutların
çözülebildiğini ve bilinen hatalı npm paketi gibi durumların kalmadığını
doğrular. Secret veya .env okumaz.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".mcp.json"


def _fail(message: str) -> int:
    print(f"❌ {message}")
    return 1


def main() -> int:
    if not CONFIG.exists():
        return _fail(".mcp.json bulunamadı")

    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    required = {"borsa", "tradingview"}
    missing = sorted(required - set(servers))
    if missing:
        return _fail(f"Eksik MCP server: {', '.join(missing)}")

    for name in sorted(required):
        cfg = servers[name]
        command = cfg.get("command")
        args = cfg.get("args", [])
        if not command or not isinstance(args, list):
            return _fail(f"{name}: command/args geçersiz")
        if command == "npx" and any("tradingview-mcp" in str(arg) for arg in args):
            return _fail(
                "tradingview: npm tradingview-mcp paketi yayından kalkmış; "
                "GitHub+uvx kullanılmalı"
            )
        resolved = shutil.which(command)
        if resolved is None and not (ROOT / command).exists():
            return _fail(f"{name}: komut bulunamadı: {command}")

    wrapper = ROOT / "scripts" / "mcp_uvx.sh"
    if not wrapper.exists():
        return _fail("scripts/mcp_uvx.sh bulunamadı")

    result = subprocess.run(
        ["bash", str(wrapper), "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return _fail(f"uvx wrapper çalışmadı: {result.stderr.strip()}")

    print("✅ MCP konfigürasyonu doğrulandı")
    return 0


if __name__ == "__main__":
    sys.exit(main())

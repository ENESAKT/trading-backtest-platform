from __future__ import annotations

import json
from pathlib import Path


def test_mcp_config_uses_working_uvx_wrapper():
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    servers = config["mcpServers"]

    assert {"borsa", "tradingview"} <= set(servers)
    for name in ("borsa", "tradingview"):
        assert servers[name]["command"] == "bash"
        assert servers[name]["args"][0] == "scripts/mcp_uvx.sh"
        assert "git+https://github.com/" in " ".join(servers[name]["args"])

    assert "npx" not in json.dumps(servers["tradingview"])

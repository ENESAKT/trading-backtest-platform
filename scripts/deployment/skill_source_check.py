#!/usr/bin/env python3
"""Validate Claude/Codex skill source layout."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAUDE = ROOT / ".claude" / "skills"
AGENTS = ROOT / ".agents" / "skills"


def main() -> int:
    claude_names = {p.name for p in CLAUDE.iterdir() if p.is_dir()}
    agent_names = {p.name for p in AGENTS.iterdir() if p.is_dir()}
    bridge_only = {name for name in agent_names if name.startswith("source-command-")}
    missing_in_agents = sorted(claude_names - agent_names - {".gitkeep"})
    missing_in_claude = sorted(agent_names - claude_names - bridge_only)
    if missing_in_agents or missing_in_claude:
        print("Skill kaynak uyumsuzluğu:")
        for name in missing_in_agents:
            print(f"  .agents aynası eksik: {name}")
        for name in missing_in_claude:
            print(f"  .claude canonical eksik: {name}")
        return 1
    print("SUCCESS: Skill kaynak düzeni tutarlı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

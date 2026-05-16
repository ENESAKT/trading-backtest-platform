#!/usr/bin/env python3
"""Production Docker context hijyen kontrolu."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCKERIGNORE = {
    ".venv",
    "frontend/node_modules",
    "frontend/dist",
    "data/cache",
    "artifacts/",
    "*.sqlite3",
}


def main() -> int:
    dockerignore = ROOT / ".dockerignore"
    if not dockerignore.exists():
        print("FAIL .dockerignore yok")
        return 1
    content = dockerignore.read_text(encoding="utf-8")
    patterns = {line.strip().rstrip("/") for line in content.splitlines() if line.strip() and not line.startswith("#")}
    missing = sorted(item for item in REQUIRED_DOCKERIGNORE if item.rstrip("/") not in patterns)
    if missing:
        print("FAIL .dockerignore eksik pattern: " + ", ".join(missing))
        return 1
    dockerfiles = [ROOT / "docker" / name for name in ("Dockerfile.api", "Dockerfile.frontend", "Dockerfile.workers")]
    absent = [str(path.relative_to(ROOT)) for path in dockerfiles if not path.exists()]
    if absent:
        print("FAIL eksik Dockerfile: " + ", ".join(absent))
        return 1
    print("OK production package: dockerignore and Dockerfiles are present")
    return 0

if __name__ == "__main__":
    sys.exit(main())

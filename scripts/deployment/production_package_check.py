#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_DOCKERIGNORE = {
    ".git",
    ".venv",
    ".venv_pdf",
    "artifacts",
    "data/cache",
    "frontend/node_modules",
    "frontend/test-results",
    "frontend/playwright-report",
}
FORBIDDEN_COPY_TOKENS = {
    "COPY data/",
    "COPY artifacts/",
    "COPY .venv",
    "COPY frontend/node_modules",
    "COPY node_modules",
}


def _dockerignore_entries() -> set[str]:
    path = ROOT / ".dockerignore"
    if not path.exists():
        return set()
    return {
        line.strip().rstrip("/")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def check_production_size() -> int:
    print("Checking production package size and docker context...")
    exit_code = 0

    entries = _dockerignore_entries()
    missing = sorted(REQUIRED_DOCKERIGNORE - entries)
    if missing:
        print("ERROR: .dockerignore eksikleri var:")
        for item in missing:
            print(f"  - {item}")
        exit_code = 1

    for dockerfile in (ROOT / "docker").glob("Dockerfile*"):
        text = dockerfile.read_text(encoding="utf-8")
        offenders = sorted(token for token in FORBIDDEN_COPY_TOKENS if token in text)
        if offenders:
            print(f"ERROR: {dockerfile.relative_to(ROOT)} yasak COPY içeriyor:")
            for token in offenders:
                print(f"  - {token}")
            exit_code = 1

    if exit_code:
        return exit_code

    print("SUCCESS: Production package checks passed.")
    return 0

if __name__ == "__main__":
    sys.exit(check_production_size())

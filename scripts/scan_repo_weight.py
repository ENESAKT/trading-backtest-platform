#!/usr/bin/env python3
"""Repo icindeki buyuk dosyalari ve runtime artifact kacagini tarar."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    ".venv_pdf",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".dart_tool",
    "cache",
    "bist",
    "viop",
    "strategy_lab",
}
RUNTIME_SUFFIXES = {".sqlite3", ".db", ".duckdb", ".parquet"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-mb", type=float, default=10.0)
    args = parser.parse_args()

    max_bytes = int(args.max_mb * 1024 * 1024)
    offenders: list[str] = []
    runtime: list[str] = []
    for path in iter_files():
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue
        rel = path.relative_to(ROOT)
        if size > max_bytes:
            offenders.append(f"{rel} ({size / 1024 / 1024:.1f} MB)")
        if path.suffix in RUNTIME_SUFFIXES:
            runtime.append(str(rel))

    if offenders or runtime:
        for item in offenders:
            print(f"LARGE {item}")
        for item in runtime:
            print(f"RUNTIME {item}")
        return 1

    print(f"OK repo weight: no files > {args.max_mb:.1f} MB and no runtime DB artifacts")
    return 0

if __name__ == "__main__":
    sys.exit(main())

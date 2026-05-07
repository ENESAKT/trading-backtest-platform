#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIRS = [
    ROOT / "backend",
    ROOT / "quant_engine",
    ROOT / "frontend" / "src",
]
EDUCATION_DIR = ROOT / "frontend" / "src" / "content" / "egitimler"


def _read_dockerignore() -> set[str]:
    path = ROOT / ".dockerignore"
    if not path.exists():
        return set()
    return {
        line.strip().rstrip("/")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _search_text(root: Path, needle: str) -> list[Path]:
    if not root.exists():
        return []
    matches: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ts", ".tsx", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle.lower() in text.lower():
            matches.append(path)
    return matches


def check_borfin_integration() -> int:
    print("--- BORFIN INTEGRATION CHECK ---")

    exit_code = 0
    dockerignore = _read_dockerignore()

    print("\nChecking artifacts/ folder:")
    artifact_root = ROOT / "artifacts"
    artifact_dirs = [
        p for p in artifact_root.iterdir()
        if artifact_root.exists() and p.is_dir() and "borfin" in p.name.lower()
    ] if artifact_root.exists() else []
    if artifact_dirs:
        if "artifacts" in dockerignore:
            print(f"  [OK] {len(artifact_dirs)} Borfin artifact klasörü production context dışında.")
        else:
            print("  [FAIL] artifacts/ .dockerignore içinde değil.")
            exit_code = 1
    else:
        print("  [OK] Borfin artifact klasörü yok.")

    print("\nChecking runtime code references...")
    runtime_matches: list[Path] = []
    for root in RUNTIME_DIRS:
        runtime_matches.extend(_search_text(root, "borfin"))
    runtime_matches = [
        p for p in runtime_matches
        if EDUCATION_DIR not in p.parents
    ]
    if runtime_matches:
        print("  [FAIL] Runtime kodunda Borfin referansı var:")
        for path in runtime_matches[:10]:
            print(f"    {path.relative_to(ROOT)}")
        exit_code = 1
    else:
        print("  [OK] Runtime kodunda Borfin bağımlılığı yok.")

    print("\nChecking education markdown references...")
    education_matches = _search_text(EDUCATION_DIR, "borfin")
    if education_matches:
        print("  [WARN] Eğitim markdown içinde Borfin adı geçiyor; birebir metin denetimi manuel göz ister:")
        for path in education_matches[:10]:
            print(f"    {path.relative_to(ROOT)}")
    else:
        print("  [OK] Eğitim markdownları Borfin adına doğrudan bağlı değil.")

    if exit_code == 0:
        print("\nSUCCESS: Borfin runtime/copyright dependency check passed.")
    return exit_code

if __name__ == "__main__":
    sys.exit(check_borfin_integration())

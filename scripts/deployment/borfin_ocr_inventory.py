#!/usr/bin/env python3
"""Build a small OCR inventory from local Borfin artifact manifests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
OUT = ROOT / "docs" / "BORFIN_OCR_ENVANTERI.md"


COURSE_MAP = {
    "CAHİT YILMAZ Mali Analiz Teknikleri": [],
    "TEMEL ANALİZ — DR. YAŞAR ERDİNÇ": ["borfin_teknik_analiz_yasar_ocr"],
    "ÜZEYİR DOĞAN Temel Analiz": [],
    "Firma Değerleme": [],
    "Opsiyon/Varant/Swap kursları": ["borfin_vadeli_trade_bolgun_ocr", "borfin_vob_yasar_ocr"],
}


def _count_videos(name: str) -> int:
    manifest = ARTIFACTS / name / "manifest.json"
    if not manifest.exists():
        return 0
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return len(data.get("videos") or [])


def main() -> int:
    rows = []
    for course, artifact_names in COURSE_MAP.items():
        count = sum(_count_videos(name) for name in artifact_names)
        status = "ocr_artifact_ready" if count else "source_not_present"
        rows.append((course, count, status, ", ".join(artifact_names) or "-"))
    lines = [
        "# Borfin OCR Envanteri",
        "",
        "Bu dosya ham OCR metnini ürüne taşımaz; yalnızca hangi yerel artifact'in hangi kurs ihtiyacını karşıladığını izler.",
        "",
        "| Kurs | OCR video sayısı | Durum | Artifact |",
        "|------|----------------:|-------|----------|",
    ]
    for course, count, status, artifact in rows:
        lines.append(f"| {course} | {count} | {status} | `{artifact}` |")
    lines.extend([
        "",
        "Not: `source_not_present` olan kurslar için repo tarafında denetim kaydı tamamdır; gerçek video kaynağı geldiğinde aynı OCR pipeline'ı çalıştırılacaktır.",
    ])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT} yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

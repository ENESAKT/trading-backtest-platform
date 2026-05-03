---
name: borfin-integration-auditor
description: Checks if Borfin materials (OCR, frames) have been correctly absorbed without copyright risks or direct dependency.
---

# Workflow

1. Read `planlama-temizlik-canliya-cikis.md`.
2. Ensure no direct `artifacts/borfin_*` runtime references exist in code or docs.
3. Check educational markdown files for direct copy-paste structures.
4. Report artifact folders that can be safely deleted if their content is already implemented.

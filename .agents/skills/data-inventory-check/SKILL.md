---
name: data-inventory-check
description: Use when checking BIST/VIOP symbol-timeframe coverage, row counts, first/last dates, retention status, or README data inventory accuracy.
---

# Workflow

1. Read `planlama-veri-platformu.md`.
2. Run `make data-inventory`.
3. Compare output with `docs/VERI_KATALOGU.md`.
4. Report missing, partial, license_required, retention_trimmed statuses.

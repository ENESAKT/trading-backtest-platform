---
name: data-retention-guardian
description: Prevents accidental retention policy violations for ClickHouse records.
---

# Workflow

1. Read `planlama-veri-platformu.md`.
2. Emphasize that BIST 1m should be kept for 365 days, and VIOP 1m for 10 years.
3. Check `scripts/check_retention.py` (if implemented) or manually verify TTL entries in ClickHouse schemas.
4. Warn the user if a schema change lowers these targets.

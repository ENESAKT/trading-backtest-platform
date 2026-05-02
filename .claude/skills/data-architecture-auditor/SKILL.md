---
name: data-architecture-auditor
description: Checks if the data architecture follows ClickHouse/MySQL/Redis separation rules.
---

# Workflow

1. Read `planlama-veri-platformu.md`.
2. Inspect `backend/data/repositories/` and `infra/`.
3. Inform the developer if there is a deviation from the storage policies (e.g. OHLCV in MySQL or relational queries in ClickHouse).
4. Run `make health-check` if needed.

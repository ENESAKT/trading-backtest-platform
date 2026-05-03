---
name: timeframe-derivation-check
description: Ensures correct derived timeframes (e.g., 5m from 1m) and avoids reverse generation.
---

# Workflow

1. Check data derivation scripts (e.g. backend/data/ingest/derive.py if implemented).
2. Ensure small timeframes only generate larger timeframes.
3. Validate that `is_derived` and `source_timeframe` are updated correctly.

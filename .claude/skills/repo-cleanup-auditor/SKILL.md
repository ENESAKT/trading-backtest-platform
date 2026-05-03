---
name: repo-cleanup-auditor
description: Checks for large files, unstructured artifacts, local DBs, and tracked runtime files before deployment.
---

# Workflow

1. Read `planlama-temizlik-canliya-cikis.md`.
2. Run `scripts/scan_repo_weight.py` or inspect the repo size.
3. Validate `.dockerignore`.
4. Ask user confirmation before deleting any significant artifact or cache file.

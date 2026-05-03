---
name: production-package-auditor
description: Checks if the Production Docker image or context is lean and clean.
---

# Workflow

1. Read `.dockerignore`.
2. Inspect `Dockerfile.api` or `piyasapilot-v2/Dockerfile.prod` definitions.
3. Ensure `.venv`, `node_modules`, and local data caches are NOT copied into the final runtime images.

---
name: deployment-readiness-check
description: Uses docs/DEPLOYMENT.md and infra/docker-compose.prod.yml to verify the server/deploy state is ready.
---

# Workflow

1. Read `docs/DEPLOYMENT.md` and `planlama-temizlik-canliya-cikis.md`.
2. Ensure backup scripts vs volumes are in place.
3. Inform the user if Domain, TLS, Env variables, or Health endpoints are missing or invalid.

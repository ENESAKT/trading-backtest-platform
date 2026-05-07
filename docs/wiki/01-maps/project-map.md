# Project Map

## Purpose

Repo, Python FastAPI backend, TypeScript/Vite frontend, quant engine, veri
platformu ve deployment dosyalarını tek çalışma alanında tutar.

## Top-Level Areas

- [[backend-map]]: FastAPI gateway, websocket bus, services, workers.
- [[frontend-map]]: Vite SPA, chart UI, strategy/paper panels.
- [[data-map]]: cache, provider, ClickHouse/MySQL/Redis ayrımı, veri klasörleri.
- [[agent-map]]: CLAUDE/AGENTS router kuralları ve yerel skills.
- [[../04-modules/quant-engine]]: backtest, strategy, research ve risk çekirdeği.
- [[../04-modules/deployment]]: Docker Compose, nginx, production kontrolleri.

## Important Entry Files

- `CLAUDE.md`
- `AGENTS.md`
- `backend/api/main.py`
- `frontend/package.json`
- `quant_engine/backtest/engine.py`
- `infra/docker-compose.yml`
- `Makefile`

## Current Shape

- `frontend/` eski `piyasapilot-v2/` içeriğinin yeni adıdır.
- `backend/signals/signal_bus.py` websocket signal fan-out için canonical yoldur.
- `docs/` proje dokümantasyonu ve bu Obsidian vault için ev sahibidir.

## Related

- [[../02-decisions/adr-0001-obsidian-project-wiki]]
- [[../03-runbooks/agent-wiki-workflow]]


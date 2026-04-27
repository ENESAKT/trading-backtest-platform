# Sub-Agents

Bu klasör projeye özel sub-agent tanımlarını içerir. Her agent ayrı bir Markdown dosyasıdır:

```
.claude/agents/<name>.md
```

## Frontmatter şablonu

```yaml
---
name: agent-adı
description: Bu agent ne işe yarar; ne zaman tetiklenir.
tools: Read, Write, Edit, Bash, Grep, Glob
model: haiku    # haiku (ucuz) | sonnet (denge) | opus (derin)
---

Agent system prompt'u burada (Markdown body).
```

## Sprint 5'te yazılacak ekip (planlama.md §7.1)

- `data-validator` — IQR spike filter testi, OHLCV doğrulama (Haiku)
- `quant-researcher` — strateji fikirleri, parametre tarama (Sonnet)
- `backtest-runner` — BacktestEngine'i çalıştır, raporla (Haiku)
- `frontend-builder` — TS/Vite/lightweight-charts (Sonnet)
- `backend-builder` — FastAPI/SQLite/worker (Sonnet)
- `robot-executor` — paper-trading otonom executor (Haiku)
- `code-reviewer` — commit öncesi kalite gate (Sonnet)
- `devops-engineer` — Docker Compose, healthcheck (Haiku)

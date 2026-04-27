# Skills

Bu klasör projeye özel skill'leri ve tradermonty/claude-trading-skills'ten kopyalanan skill'leri içerir.

```
.claude/skills/<skill-name>/SKILL.md
```

## Frontmatter şablonu

```yaml
---
name: skill-adı
description: Skill ne işe yarar (otomatik invocation için).
disable-model-invocation: false
allowed-tools: Read, Bash(pytest *)
model: inherit
---

Skill prompt body burada.
```

## Sprint 5'te kurulacak skill seti (planlama.md §7.2)

### tradermonty'den kopyalananlar
- `backtest-expert`, `position-sizer`, `technical-analyst`
- `market-news-analyst`, `signal-postmortem`
- `strategy-pivot-designer`, `scenario-analyzer`, `exposure-coach`

### Projeye özel
- `validate-spike-filter`, `run-backtest`, `health-check`
- `morning-briefing`, `paper-trade-status`, `deploy-stack`, `session-recap`

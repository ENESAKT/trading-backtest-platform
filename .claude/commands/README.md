# Slash Commands

Bu klasör `/komut` slash command tanımlarını içerir.

```
.claude/commands/<name>.md
```

## Frontmatter şablonu

```yaml
---
description: Komut ne yapar (status bar'da görünür).
argument-hint: "[symbol] [start-date] [end-date]"
allowed-tools: Bash(python *), Read, Write
model: inherit
---

Prompt body. $1, $2 gibi argümanlar.
```

## Sprint 5'te yazılacak komutlar (planlama.md §7.5)

- `/devam` — son `session-recap.md`'yi yükle, kalınan yerden başla
- `/backtest <sembol> <strateji> <başlangıç> <bitiş>` — backtest-runner agent'ını tetikle
- `/sinyal <sembol>` — DecisionEngine + Claude API hibrit sinyal raporu
- `/durum` — tüm servislerin sağlık özeti
- `/strateji-yeni` — quant-researcher agent'ını başlat

# Hooks

Bu klasör shell script formundaki hook'ları tutar. Hook'lar `.claude/settings.json` üzerinden bağlanır.

## Sprint 5'te kurulacak 5 hook (planlama.md §7.4)

| Event | Hook | Amaç |
|-------|------|------|
| `SessionStart` | `check-services.sh` | Docker + cache + planlama.md durumunu kontrol et |
| `UserPromptSubmit` | `load-recent-state.sh` | `session-recap.md`'yi sistem mesajı olarak inject et |
| `PostToolUse` (Edit/Write) | `lint.sh` | `ruff check --fix` + `npm run lint` |
| `SubagentStop` | `persist-agent-output.sh` | Agent çıktısını `.claude/agent-logs/` altına yaz |
| `Stop` | `auto-recap.sh` | `session-recap.md`'yi yenile, `planlama.md` checkbox'larını güncelle |

## Hook script formatı

```bash
#!/bin/bash
# .claude/hooks/example.sh
# stdin: JSON event payload
# stdout: opsiyonel JSON systemMessage
# exit 0: devam | exit 2: blok et + stderr'i kullanıcıya göster
```

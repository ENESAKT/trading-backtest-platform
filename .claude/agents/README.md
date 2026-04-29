# Sub-Agents

Bu klasor projeye ozel sub-agent tanimlari icindir. Su an aktif agent yoktur.

Guvenli varsayilan:

- Agent sayisini az tut: ayni anda 1-2 agent yeterlidir.
- Model: `sonnet` veya ucuz isler icin `haiku`; `opus` kullanma.
- `Write`, `Edit`, `Bash`, `Task` yalnizca acik gerekceyle verilir.
- Agent test, commit, push, PR, merge veya auto-merge yapmaz.
- Agent buyuk dosya/klasor okumaz: `node_modules`, `.git`, `.pytest_cache`,
  SQLite/DB, lock dosyalari.
- Agent sonucu kisa ozetler; tum loglari ana context'e basmaz.

## Frontmatter sablonu

```yaml
---
name: agent-adi
description: Ne zaman kullanilacagini dar ve net yaz.
tools: Read, Grep, Glob
model: sonnet
---
```

`Bash`, `Write`, `Edit` veya `Task` gerekiyorsa neden gerektigini agent body
icinde yaz ve Enes onayi olmadan test/commit/PR/merge yapmayacagini belirt.

## Ertelenen sprint fikri

Eski plan 8 agent oneriyordu. Bu repo icin daha guvenli yaklasim:

- `backend-helper` - sadece hedefli backend okuma/onerme.
- `frontend-helper` - sadece hedefli frontend okuma/onerme.
- `review-helper` - sadece diff inceleme, test veya git islemi yok.

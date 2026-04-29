# Slash Commands

Bu klasor slash command tanimlari icindir. Su an aktif command yoktur.

Guvenli varsayilan:

- Komutlar once plan/ozet uretir; dogrudan kod yazmaz.
- Test, build, dev server, commit, push, PR ve merge komutlari onay ister.
- Agent baslatan komutlar tek agent ile sinirli kalir.
- Cok dosya okutan komutlar once hangi dosyalari okuyacagini listeler.

## Frontmatter sablonu

```yaml
---
description: Komutun dar amaci.
argument-hint: "[opsiyonel-arguman]"
allowed-tools: Read, Grep, Glob
model: inherit
---
```

`Bash`, `Write`, `Edit` izinleri varsayilan sablonda yoktur.

## Guvenli komut fikirleri

- `/durum-guvenli` - `git status` ve kisa dosya listesi; test yok.
- `/planla` - en fazla 3 dosya secip plan cikarir.
- `/handoff-kisa` - mevcut durumu 20-30 satirda ozetler.

---
name: "source-command-devam"
description: "Bir önceki oturumdan kaldığın yerden devam et"
---

# source-command-devam

Use this skill when the user asks to run the migrated source command `devam`.

## Command Template

# /devam

Bir önceki oturumun `session-recap.md`'sini yükle ve kaldığın yerden başla.

## Adımlar

1. `.Codex/memory/session-recap.md` dosyasını oku (varsa)
2. `planlama.md` dosyasını oku — Sprint listesinden ilk açık (`- [ ]`) tick'i bul
3. `ogrenilenler.md` dosyasını oku — son öğrenilen dersleri hatırla
4. `git log --oneline -10` çalıştır — son commit'leri kontrol et
5. Sıradaki görevin ne olduğunu özetle ve onay iste

## Bağlam

Bu komut yeni bir Codex oturumu açıldığında ilk çağrılacak komuttur. Amaç: context kaybını önlemek, projeyi sıfırdan keşfetmek yerine dokümantasyondan devam etmek.

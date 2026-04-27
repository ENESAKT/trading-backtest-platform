# Memory (Oturumlar Arası Bellek)

Bu klasör, oturum geçişlerinde context'i kaybetmemek için kullanılan dosyaları tutar.

## Beklenen dosyalar (Sprint 5'te otomasyonu kurulacak)

- **`session-recap.md`** — `Stop` hook'u her oturum sonunda otomatik yazar:
  - Son commit'ler (git log özeti)
  - Tamamlanan checkbox'lar
  - Tool kullanım sayıları
  - Açık kalan iş
  - Sıradaki Sprint adımı
- **`agent-logs/<agent-name>/<timestamp>.json`** — `SubagentStop` hook'u sub-agent çıktılarını biriktirir.

## Yeni oturum açıldığında

`SessionStart` hook → `load-recent-state.sh` → `session-recap.md`'yi systemMessage olarak inject eder. Yeni Claude penceresi sıfırdan repo keşfi yapmadan kaldığı yerden devam eder.

Detay: `planlama.md` §8 (Memory & Context Persistence).

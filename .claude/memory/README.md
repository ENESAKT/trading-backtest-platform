# Memory

Bu klasor oturumlar arasi kisa ozetler icindir. Su an aktif otomatik memory
hook'u yoktur.

Guvenli varsayilan:

- Memory dosyalari otomatik systemMessage olarak inject edilmez.
- Ozetler 30-50 satirla sinirli tutulur.
- Agent loglari ana context'e otomatik eklenmez.
- Tool loglari, full diff, test ciktisi ve uzun plan dosyalari memory'ye
  kopyalanmaz.

Onerilen dosyalar:

- `session-recap.md` - manuel, kisa son durum.
- `handoff.md` - manuel, bir sonraki oturum icin net adimlar.

Yeni oturumda once kullanici istegi dinlenir; memory yalnizca gerekirse okunur.

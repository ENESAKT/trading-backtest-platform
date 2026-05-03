# PiyasaPilot Ajan Rehberi

Bu repo, geliştirme sürecini ve operasyonel denetimi desteklemek için özel Claude Ajanları kullanır. Ajanlar, kullanıcının sistemi anlamasına ve geliştirirken hata yapmamasına yardımcı olur.

## Aktif Ajanlar

### 1. `data-platform-mentor`
**Yol:** `.claude/agents/data-platform-mentor.md`
**Görev:** Kullanıcıya veri platformunu Türkçe, adım adım ve projeden (`PiyasaPilot`) örneklerle öğretir. Karmaşık ClickHouse, MySQL ve Redis konularını basit anlatır.

### 2. `data-architect`
**Yol:** `.claude/agents/data-architect.md`
**Görev:** Veri mimarisi (ClickHouse/MySQL/Redis sınırları) ihlal edilmeden kod yazılmasını sağlar. Veritabanı operasyonlarını planlar.

### 3. `release-janitor`
**Yol:** `.claude/agents/release-janitor.md`
**Görev:** Canlıya çıkış (Production) öncesi Docker paket boyutu kontrolü, dosya temizliği ve yedekleme denetimi gibi operasyonları üstlenir. İzin almadan dosya silmez.

## Nasıl Kullanılır?
Gelecekte herhangi bir task için bu ajanların profiline bürünmek istenirse `ACT MODE`'da ajan profili içeriği context olarak referans alınabilir.

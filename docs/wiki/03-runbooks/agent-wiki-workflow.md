# Agent Wiki Workflow

## Purpose

Bu çalışma akışı, ajanların Obsidian wiki'yi proje hafızası olarak kullanmasını
sağlar.

## Query Before Coding

1. `docs/wiki/index.md` dosyasını oku.
2. Göreve en yakın map notunu aç.
3. Map notundaki source file listesinden sadece gerekli dosyaları incele.
4. Kod değişikliği yapacaksan koruma listesini kontrol et.

## Ingest After Changes

1. `git diff --name-only` ile değişen dosyaları gör.
2. Değişen alanın map veya module notunu bul.
3. En fazla birkaç maddeyle yeni gerçeği yaz.
4. İlgili notlara Obsidian linki ekle.

## Lint Monthly Or On Request

1. `rg "\\[\\[" docs/wiki` ile wiki linklerini tara.
2. Dosya yolları ve mimari iddiaları mevcut repo ile karşılaştır.
3. Eski iddiaları düzelt, değerli kararları archive et.
4. Büyük transcript veya log saklama.

## Prompt Pattern

```text
docs/wiki/index.md dosyasından başla. İlgili wiki notlarını oku, sonra sadece
gerekli kaynak dosyaları incele. Kod yapımı bozmadan plan çıkar veya değişikliği
uygula. İş bitince ilgili wiki notunu güncelle.
```

## Related

- [[../01-maps/agent-map]]
- [[../02-decisions/adr-0001-obsidian-project-wiki]]


# ADR 0001: Obsidian Project Wiki

## Status

Accepted

## Context

Büyük kod tabanını her görevde baştan okutmak token maliyetini ve yanlış bağlam
riskini artırır. Video kaynağındaki yaklaşım, kod tabanını insan tarafından da
okunabilir bir Obsidian wiki ağına dönüştürmeyi önerir.

## Decision

Backtest reposunda Obsidian vault olarak `docs/wiki/` kullanılacak.
Bu vault üretim kodundan ayrı kalacak ve repo klasör yapısını bozmayacak.

## Consequences

- Ajanlar geniş keşiften önce wiki haritalarını okuyabilir.
- Mimari kararlar düz Markdown olarak incelenebilir.
- Kod değiştikçe wiki notlarının güncellenmesi gerekir.
- Wiki, RAG/veritabanı yerine geçmez; proje hafızası ve navigasyon katmanıdır.

## Related

- [[../03-runbooks/agent-wiki-workflow]]
- [[../_meta/video-obsidian-claude-mimarisi]]


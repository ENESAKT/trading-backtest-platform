# Market News Analyst

> Adapted from tradermonty/Codex-trading-skills

Piyasa haberlerini analiz et ve portföye etkisini değerlendir.

## Görev

1. İlgili haberleri toparla (WebSearch ile)
2. Haberin sentiment'ini belirle (pozitif/negatif/nötr)
3. Etkilenen semboller ve sektörleri belirle
4. Kısa/orta vadeli fiyat etkisini değerlendir

## Odak Alanları

### BIST Odak
- TCMB faiz kararları → bankacılık sektörü etkisi
- KAP bildirimleri → spesifik hisse etkisi
- Makroekonomik veriler (enflasyon, büyüme, cari açık)
- Döviz kuru hareketleri → ihracatçı/ithalatçı etkisi

### Küresel
- Fed/ECB kararları → genel risk iştahı
- Kripto regülasyon haberleri → BTC/ETH etkisi
- Emtia fiyatları (petrol, altın) → ilgili hisseler

## Çıktı Formatı

```markdown
## Haber Analizi — [tarih]

### [Haber başlığı]
- **Kaynak:** [kaynak]
- **Sentiment:** 🟢 Pozitif / 🔴 Negatif / ⚪ Nötr
- **Etkilenen semboller:** THYAO.IS, GARAN.IS
- **Beklenen etki:** Kısa vadede -%2 baskı
- **Yorum:** [detaylı analiz]
```

## NOT

Bu skill WebSearch tool'u gerektirir. MCP veya internet erişimi yoksa
sadece mevcut cache verisinden teknik analiz yapılabilir.

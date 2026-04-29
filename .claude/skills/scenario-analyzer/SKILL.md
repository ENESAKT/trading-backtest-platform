# Scenario Analyzer

> Adapted from tradermonty/claude-trading-skills

Piyasa senaryolarını analiz et ve portföy etkisini değerlendir.

## Görev

Belirli bir piyasa senaryosunun gerçekleşmesi durumunda portföy üzerindeki etkiyi analiz et.

## Senaryo Tipleri

1. **Makro Senaryolar:**
   - TCMB faiz artırımı / indirimi
   - USD/TRY şok hareket (%5+)
   - Küresel resesyon riski
   - Fed politika değişikliği

2. **Sektör Senaryoları:**
   - Bankacılık regülasyon değişikliği
   - Enerji fiyatları şoku
   - Teknoloji satışı
   - Savunma harcamaları artışı

3. **Teknik Senaryolar:**
   - XU100 destek kırılımı
   - BTC halvening etkisi
   - Altın rekor seviye
   - Volatilite spike (VIX > 30)

## Analiz Çerçevesi

Her senaryo için:
1. **Olasılık:** Düşük / Orta / Yüksek
2. **Etki:** Portföy değer değişimi tahmini
3. **Etkilenen varlıklar:** Sembol bazlı etki tablosu
4. **Hedge önerisi:** Riski azaltmak için yapılabilecekler
5. **Aksiyon:** AL / SAT / TUT / HEDGE önerisi

## Çıktı

```markdown
## Senaryo: [açıklama]

| Varlık | Mevcut Ağırlık | Beklenen Etki | Aksiyon |
|--------|---------------|---------------|---------|
| THYAO.IS | %10 | +5% | TUT |
| GARAN.IS | %8 | -12% | AZALT |
```

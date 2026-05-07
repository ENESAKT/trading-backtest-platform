---
title: İleri HO Türleri: DEMA, TEMA, HMA, T3
slug: ileri-ho-turleri
category: indikatorler
tags: [trend, hareketli ortalama, dema, tema, hma, t3]
difficulty: ileri
indicator_key: DEMA, TEMA, HMA, T3
related_strategies: []
source_courses: [kivanc_hareketli_ortalamalar, fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, whipsaw, parametre_overfit]
copy_policy: original_piyasapilot_content
---

İleri hareketli ortalamalar, klasik SMA ve EMA'nın gecikme ile gürültü dengesini iyileştirmeye çalışan varyasyonlardır. DEMA ve TEMA gecikmeyi azaltmaya, HMA daha pürüzsüz ama hızlı tepki vermeye, T3 ise daha yumuşak trend takibine odaklanır.

## Nedir?

Bu ortalamaların ortak hedefi fiyatı daha okunur hale getirmektir. Fakat daha hızlı tepki almak her zaman daha iyi sinyal demek değildir; hız arttıkça yanlış dönüş riski de artabilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de kavramsal çağrılar:

```text
DEMA(C,21)
TEMA(C,21)
HMA(C,21)
T3(C,21,0.7)
```

Trend filtresi örneği:

```text
C > HMA(C,55) AND HMA(C,21) > HMA(C,55)
```

## Nasıl Okunur?

DEMA ve TEMA, EMA'ya göre daha hızlı dönebilir. HMA kısa vadeli trend değişimini daha okunur hale getirebilir. T3 ise gereksiz titreşimi azaltmayı hedefler; daha sakin ama bazen daha geç davranır.

## Kullanım Örneği

Kısa vadeli sistemde fiyat HMA 21 üstüne çıkıp HMA 21 de HMA 55'in üzerine yerleşirse trend devamı senaryosu kurulabilir. Daha sakin bir sistemde T3 yön değişimi, daha az işlem üreten bir filtre olarak denenebilir.

## Tuzaklar ve Riskler

- Daha gelişmiş ortalama, daha iyi performans garantisi vermez.
- Parametre sayısı arttıkça overfit riski büyür.
- Hızlı ortalamalar yatay piyasada sık whipsaw üretebilir.
- Aynı anda çok sayıda ortalama kullanmak sinyali netleştirmek yerine karıştırabilir.

## PiyasaPilot'ta Kullan

Bu sürümde doğrudan grafik köprüsü yok. PiyasaPilot'ta ileri HO türlerini klasik EMA stratejilerinin yerine birebir koymak yerine, önce aynı veri setinde işlem sayısı, max drawdown ve out-of-sample davranışıyla karşılaştırmak gerekir.

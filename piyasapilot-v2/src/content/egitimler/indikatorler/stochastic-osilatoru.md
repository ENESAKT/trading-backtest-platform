---
title: Stochastic Osilatörü
slug: stochastic-osilatoru
category: indikatorler
tags: [momentum, osilatör, aşırı alım, aşırı satım, dönüş]
difficulty: orta
indicator_key: STOCH
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, trendde_erken_sinyal, yatay_esik_yanilmasi]
copy_policy: original_piyasapilot_content
---

Stochastic Osilatörü, kapanışın son fiyat aralığı içinde nereye yerleştiğini gösteren bir momentum aracıdır. Fiyat aralığın üst kısmında kapanıyorsa alıcıların, alt kısmında kapanıyorsa satıcıların daha baskın olduğu okunabilir.

## Nedir?

Stochastic, genellikle iki çizgiyle izlenir: hızlı çizgi fiyatın aralık içindeki konumunu, yavaş çizgi bu hareketin yumuşatılmış halini gösterir. 80 üzeri ve 20 altı bölgeler dikkat alanıdır, fakat tek başına emir sebebi değildir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel okuma şöyle düşünülebilir:

```text
STOCH_K(H,L,C,14,3)
STOCH_D(H,L,C,14,3,3)
```

Basit bir dönüş kuralı:

```text
CROSS_UP(STOCH_K(H,L,C,14,3), STOCH_D(H,L,C,14,3,3)) AND STOCH_K(H,L,C,14,3) < 25
```

Bu kural, osilatör düşük bölgede toparlanırken çizgilerin yukarı kesişmesini arar.

## Nasıl Okunur?

20 altından yukarı dönüş kısa vadeli tepki ihtimalini artırabilir. 80 üstünden aşağı dönüş ise momentumun yorulduğunu gösterebilir. Ana trend yukarıysa düşük bölgedeki dönüşler, ana trend aşağıysa yüksek bölgedeki zayıflamalar daha anlamlıdır.

## Kullanım Örneği

Fiyat EMA 50 üzerinde kalırken Stochastic 20 altından yukarı dönerse, kısa vadeli geri çekilmenin bittiği bir toparlanma senaryosu kurulabilir. Aynı sinyal EMA 200 altında ve düşen trendde gelirse sadece zayıf bir tepki olabilir.

## Tuzaklar ve Riskler

- Güçlü trendlerde osilatör uzun süre uç bölgede kalabilir.
- 80 üzeri otomatik satış, 20 altı otomatik alış anlamına gelmez.
- Çok kısa ayarlar sık kesişim ve gürültü üretir.
- Sinyal, hacim veya trend filtresi olmadan kolayca whipsaw'a dönebilir.

## PiyasaPilot'ta Kullan

Bu konu için doğrudan grafik köprüsü henüz açılmadı. StrategySpec tarafında Stochastic fikrini momentum dönüş kuralı olarak yazıp EMA veya ATR filtresiyle test etmek daha güvenli bir başlangıçtır.

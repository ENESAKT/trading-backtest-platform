---
title: CCI — Emtia Kanal Endeksi
slug: cci
category: indikatorler
tags: [momentum, osilatör, kanal, aşırı bölge]
difficulty: orta
indicator_key: CCI
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, trendde_erken_sinyal, esik_yanilmasi]
copy_policy: original_piyasapilot_content
---

CCI, fiyatın kendi ortalama davranışından ne kadar saptığını ölçen bir osilatördür. Adında emtia geçse de hisse, endeks ve vadeli piyasalarda da momentum sapmasını okumak için kullanılabilir.

## Nedir?

CCI sıfır çizgisi etrafında dolaşır; pozitif bölgeler fiyatın ortalamanın üstünde, negatif bölgeler ise ortalamanın altında hareket ettiğini gösterir. Çok yüksek veya çok düşük değerler güçlü momentum ya da yorulma sinyali olabilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri:

```text
CCI(H,L,C,20)
```

Dönüş fikri:

```text
CROSS_UP(CCI(H,L,C,20), -100) AND C > EMA(C,50)
```

Bu kural, CCI'ın zayıf bölgeden yukarı toparlanmasını ve fiyatın ana trend filtresinin üzerinde kalmasını arar.

## Nasıl Okunur?

CCI'ın 100 üstüne çıkması momentumun güçlendiğini, -100 altına inmesi satış baskısının arttığını gösterebilir. Trend yukarıysa -100 bölgesinden dönüşler, trend aşağıysa 100 üstünden zayıflamalar daha anlamlıdır.

## Kullanım Örneği

Fiyat EMA 50 üzerinde tutunurken CCI -100 altından yukarı dönerse geri çekilmenin bittiği bir tepki senaryosu kurulabilir. Aynı sinyal düşen ana trendde oluşursa sadece kısa süreli tepki olarak ele alınmalıdır.

## Tuzaklar ve Riskler

- Güçlü trendlerde CCI uzun süre uç bölgede kalabilir.
- Sabit 100/-100 eşikleri her sembolde aynı çalışmaz.
- Kısa periyot daha hızlı ama daha gürültülü sinyal üretir.
- CCI yön teyidi değil, momentum sapması göstergesidir.

## PiyasaPilot'ta Kullan

Doğrudan grafik köprüsü bu sürümde yok. StrategySpec içinde CCI'ı tek başına giriş sinyali yapmak yerine EMA veya ADX gibi trend filtresiyle birlikte kullanmak daha güvenli bir başlangıçtır.

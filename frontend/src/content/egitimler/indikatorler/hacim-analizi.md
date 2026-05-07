---
title: Hacim Analizi
slug: hacim-analizi
category: indikatorler
tags: [hacim, likidite, teyit, katılım]
difficulty: başlangıç
indicator_key: VOL
chart_indicator: vol
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [likidite, tek_bar_sicramasi, veri_kalitesi]
copy_policy: original_piyasapilot_content
---

Hacim, fiyat hareketine kaç işlem biriminin eşlik ettiğini gösterir. Teknik analizde çoğu zaman fiyatın yanında ikinci gerçeklik kontrolü gibi kullanılır: hareket var mı, bu harekete katılım var mı?

## Nedir?

Yükselen fiyatın artan hacimle gelmesi katılımı güçlendirebilir. Fiyat yükselirken hacim düşüyorsa hareket zayıf kalabilir. Düşüşte hacim artışı ise satış baskısının ciddiyetini gösterebilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de ham hacim ve ortalama hacim:

```text
V
SMA(V,20)
```

Basit teyit filtresi:

```text
C > HIGHEST(C,20) AND V > SMA(V,20) * 1.5
```

Bu kural fiyat kırılımının sıradan hacimle mi, belirgin katılımla mı geldiğini ayırmaya çalışır.

## Nasıl Okunur?

Hacim kendi başına yön söylemez. Fiyatın bulunduğu bölgeyle birlikte okunmalıdır: direnç kırılımında yüksek hacim olumlu, destek kırılımında yüksek hacim riskli olabilir. Düşük hacimde oluşan sinyaller daha kolay bozulur.

## Kullanım Örneği

Bir hisse uzun süredir yatay bantta beklerken fiyat direnç üstüne çıkar ve hacim 20 günlük ortalamanın belirgin üstüne taşarsa, hareketin takip edilme olasılığı artar. Aynı kırılım düşük hacimle gelirse teyit beklemek daha sağlıklıdır.

## Tuzaklar ve Riskler

- Tek seferlik blok işlem hacmi göstergeleri şişirebilir.
- Düşük likiditeli sembollerde hacim sinyali çok gürültülüdür.
- Hacim artışı yön değil, katılım gösterir.
- Farklı piyasalarda hacim verisinin kapsamı değişebilir.

## PiyasaPilot'ta Kullan

Grafikte hacim panelini açarak fiyat hareketinin katılımla desteklenip desteklenmediğini izleyebilirsin. Backtest tarafında hacmi giriş sinyali değil, kırılım veya trend kurallarını filtreleyen teyit olarak kullanmak daha güvenlidir.

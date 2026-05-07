---
title: Volume Price Trend ve Volume Oscillator
slug: volume-price-trend-volume-oscillator
category: indikatorler
tags: [hacim, vpt, hacim osilatörü, teyit]
difficulty: orta
indicator_key: VPT, VOSC
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [hacim_verisi, likidite, uyumsuzluk_yanilmasi]
copy_policy: original_piyasapilot_content
---

Volume Price Trend, fiyat değişimini hacimle ağırlıklandırarak kümülatif bir katılım çizgisi üretir. Volume Oscillator ise kısa ve uzun hacim ortalamaları arasındaki farkı izleyerek hacim rejiminin hızlanıp hızlanmadığını gösterir.

## Nedir?

VPT, fiyat yönüyle hacim akışını birlikte okumaya çalışır. Volume Oscillator ise hacmin kendi ortalamasına göre canlanıp canlanmadığını anlatır. Biri fiyatla hacim ilişkisini, diğeri hacim temposunu öne çıkarır.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seriler:

```text
VPT(C,V)
VOSC(V,14,28)
```

Kırılım teyidi:

```text
C > HIGHEST(C,20) AND VPT(C,V) > HIGHEST(VPT(C,V),20) AND VOSC(V,14,28) > 0
```

## Nasıl Okunur?

Fiyat yükselirken VPT de yükseliyorsa katılım fiyatı destekliyor olabilir. Volume Oscillator sıfır üstüne çıkıyorsa son hacim temposu uzun ortalamaya göre hızlanmıştır. İkisi birlikte kırılım teyidinde faydalıdır.

## Kullanım Örneği

Bir direnç kırılımında fiyat yeni zirve yapar, VPT de yeni zirveye eşlik eder ve VOSC sıfır üstüne dönerse hareket daha güçlü görünür. Fiyat kırılıp VPT geride kalıyorsa sinyalin kalitesi düşer.

## Tuzaklar ve Riskler

- Hacim verisi kötü ise iki gösterge de yanıltıcıdır.
- VPT kümülatif olduğu için geçmişteki yüksek hacimli barlardan etkilenir.
- VOSC kısa vadeli hacim sıçramalarını abartabilir.
- Hacim teyidi fiyat riskini ortadan kaldırmaz; stop kuralı yine gerekir.

## PiyasaPilot'ta Kullan

Doğrudan grafik köprüsü yok. PiyasaPilot'ta VPT ve VOSC'yi fiyat kırılımı ya da trend devamı kurallarına hacim filtresi olarak eklemek en anlamlı kullanımdır.

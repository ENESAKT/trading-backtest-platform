---
title: Hareketli Ortalamalar: SMA ve EMA
slug: sma-ema
category: indikatorler
tags: [trend, ortalama, sma, ema, kesişim]
difficulty: başlangıç
indicator_key: EMA, SMA
chart_indicator: ema
related_strategies: [sma_crossover]
source_courses: [kivanc_hareketli_ortalamalar, fuat_akman_indikator]
source_method: frame_ocr
source_confidence: medium
needs_audio_transcript: true
risk_warnings: [gecikme, whipsaw, periyot_uyumsuzlugu]
copy_policy: original_piyasapilot_content
---

Hareketli ortalama, fiyatın kısa vadeli gürültüsünü azaltıp ana yönü daha okunur hale getirir. SMA tüm periyotlara eşit ağırlık verir; EMA son fiyatlara daha fazla ağırlık verdiği için daha hızlı tepki verir.

## Nedir?

SMA daha sakin ve gecikmeli, EMA daha duyarlı ve gürültüye açıktır. Kısa ortalama uzun ortalamayı yukarı kestiğinde momentum güçlenebilir; aşağı kestiğinde trend zayıflayabilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de iki temel seri:

```text
SMA(C,50)
EMA(C,50)
```

Kesişim stratejisi:

```text
CROSS_UP(EMA(C,50), EMA(C,200))
```

Çıkış kuralı:

```text
CROSS_DOWN(EMA(C,50), EMA(C,200))
```

## Nasıl Okunur?

Kısa periyotlar hızlı sinyal üretir, uzun periyotlar daha geç ama daha sakin davranır. Günlük grafikte 20/50 daha orta vade, 50/200 daha ana trend filtresi gibi okunabilir.

## Kullanım Örneği

Fiyat EMA 50 üzerinde kalırken EMA 50'nin EMA 200'ü yukarı kesmesi trend takip için bir başlangıç sinyalidir. Ancak yatay piyasada bu kesişimler sık bozulur; bu yüzden hacim veya ATR filtresi eklemek mantıklıdır.

## Tuzaklar ve Riskler

- Ortalamalar fiyatı takip eder, fiyatı önden bilmez.
- Yatay piyasada sık kesişim zarar serisi yaratabilir.
- Periyot, grafiğin zaman dilimiyle uyumlu seçilmelidir.
- Sadece en iyi geçmiş sonucu veren periyot canlıda kırılgan olabilir.

## PiyasaPilot'ta Kullan

Grafikte EMA katmanını açıp kısa ve orta trend davranışını izleyebilirsin. Backtest tarafında `sma_crossover`, ortalama kesişimini komisyon ve slippage ile birlikte ölçer.

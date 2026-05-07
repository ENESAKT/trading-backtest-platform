---
title: MACD
slug: macd
category: indikatorler
tags: [momentum, trend, histogram, ema]
difficulty: orta
indicator_key: MACD
chart_indicator: macd
related_strategies: [macd_divergence]
source_courses: [fuat_akman_indikator, kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, yatay_piyasa, gec_teyit]
copy_policy: original_piyasapilot_content
---

MACD, iki üssel hareketli ortalama arasındaki farkı ve bu farkın sinyal çizgisiyle ilişkisini izler. Trend momentumu için kullanışlıdır; yatay piyasada ise sık sık yanlış kesişim üretebilir.

## Nedir?

MACD çizgisi hızlı ve yavaş EMA farkını, sinyal çizgisi bu farkın yumuşatılmış halini, histogram ise ikisi arasındaki mesafeyi gösterir. Histogramın sıfır çevresindeki davranışı momentum değişimini daha erken okumaya yardım eder.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de standart okuma:

```text
MACD_LINE(C,12,26,9)
MACD_SIGNAL(C,12,26,9)
MACD_HIST(C,12,26,9)
```

Basit bir tetikleyici:

```text
CROSS_UP(MACD_HIST(C,12,26,9), 0) AND C > EMA(C,50)
```

## Nasıl Okunur?

Histogram negatiftan pozitife dönerken fiyat kısa trend filtresinin üzerindeyse momentum toparlanıyor olabilir. MACD çizgisi sinyal çizgisini aşağı keserse trend gücü zayıflıyor olabilir.

## Kullanım Örneği

Geniş bir düşüşten sonra fiyat EMA 50 üzerine çıkar, MACD histogramı da sıfır üstüne dönerse ilk toparlanma denemesi oluşur. Bu sinyal genellikle RSI'a göre daha geç gelir, ama trend yönüyle uyumlu olduğunda daha düzenli çalışabilir.

## Tuzaklar ve Riskler

- MACD gecikmeli bir göstergedir; dip ve tepe yakalama aracı değildir.
- Sıkışık yatay piyasada çok sayıda küçük zarar üretebilir.
- Tek kesişim yerine trend, hacim ve volatiliteyle teyit aranmalıdır.
- Parametreleri sembole göre aşırı optimize etmek canlı performansı bozabilir.

## PiyasaPilot'ta Kullan

Grafikte MACD alt panelini açıp çizgi, sinyal ve histogram davranışını birlikte izle. Backtest tarafındaki `macd_divergence` preset'i histogram sıfır dönüşünü ölçülebilir hale getirir.

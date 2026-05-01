---
title: Bollinger Bandı
slug: bollinger-bandi
category: indikatorler
tags: [volatilite, bant, mean-reversion, standart sapma]
difficulty: başlangıç
indicator_key: BB
chart_indicator: bb
related_strategies: [bollinger_reversion]
source_courses: [fuat_akman_indikator, kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, bant_yanilmasi, trendde_ters_sinyal]
copy_policy: original_piyasapilot_content
---

Bollinger Bandı, fiyatın son dönem ortalamasından ne kadar uzaklaştığını volatiliteyle birlikte gösterir. Orta çizgi genellikle hareketli ortalama, üst ve alt çizgiler ise bu ortalamanın etrafındaki değişken oynaklık alanıdır.

## Nedir?

Bandın genişlemesi piyasadaki hareket alanının büyüdüğünü, daralması ise sıkışmanın arttığını gösterir. Bant teması tek başına al veya sat emri değildir; trend yönü, hacim ve momentumla birlikte okunmalıdır.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de aynı fikri üç çizgiyle düşünebilirsin:

```text
BB_MID(C,20,2)
BB_UPPER(C,20,2)
BB_LOWER(C,20,2)
```

Orta çizgi kapanışların hareketli ortalamasını, üst ve alt çizgiler ise standart sapma katsayısıyla genişleyen sınırları temsil eder.

## Nasıl Okunur?

Alt banda sarkan ve tekrar bandın içine dönen fiyat, zayıflayan satış baskısına işaret edebilir. Üst banda sürekli yapışan fiyat ise bazen pahalı görünmesine rağmen güçlü trendin sürdüğünü gösterir.

## Kullanım Örneği

Yatay ya da hafif eğimli piyasada alt banttan içeri dönüş, orta banda kadar kısa vadeli bir tepki senaryosu üretir. Trend güçlü aşağıysa aynı sinyal erken olabilir; bu yüzden EMA 50 veya RSI 50 gibi ek filtreler kullanmak daha sağlıklıdır.

## Tuzaklar ve Riskler

- Güçlü trendde fiyat banda uzun süre yapışabilir.
- Standart sapma geçmiş veriye bakar; ani haber hareketlerinde gecikir.
- Bant daralması kırılım yönünü söylemez, sadece sıkışmayı görünür yapar.
- Parametreyi geçmişe göre fazla iyileştirmek overfit üretir.

## PiyasaPilot'ta Kullan

Grafikte BB katmanını açıp bant davranışını canlı mumlarla izleyebilirsin. Backtest tarafında `bollinger_reversion` preset'i, alt bant dönüşünü test edilebilir bir başlangıç kuralına çevirir.

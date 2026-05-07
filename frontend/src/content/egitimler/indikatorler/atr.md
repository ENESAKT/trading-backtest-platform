---
title: ATR — Ortalama Gerçek Aralık
slug: atr
category: indikatorler
tags: [volatilite, stop, risk, supertrend]
difficulty: orta
indicator_key: ATR
chart_indicator: atr
related_strategies: [supertrend]
source_courses: [fuat_akman_indikator, kivanc_algo_trade]
source_method: frame_ocr
source_confidence: medium
needs_audio_transcript: true
risk_warnings: [gecikme, haber_sicramasi, stop_mesafesi]
copy_policy: original_piyasapilot_content
---

ATR, fiyatın yönünü değil hareket aralığını ölçer. Bu yüzden trend sinyali üretmekten çok stop mesafesi, pozisyon büyüklüğü ve volatilite rejimi için kullanılır.

## Nedir?

ATR yükseliyorsa piyasanın günlük veya seçili periyot içi hareket alanı genişliyordur. ATR düşüyorsa fiyat daha dar bir bantta hareket ediyor olabilir. Yön bilgisi vermediği için mutlaka fiyat yapısıyla birlikte okunmalıdır.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de ATR serisi:

```text
ATR(14)
```

Volatilite filtresi örneği:

```text
C > EMA(C,50) AND ATR(14) > LOWEST(ATR(14),20)
```

Bu kural trend yönünü EMA ile, hareket alanının canlanmasını ATR ile kontrol eder.

## Nasıl Okunur?

ATR'nin yükselmesi hareket fırsatı doğurabilir ama aynı zamanda stop mesafesinin genişlemesi gerektiğini söyler. ATR düşükken dar stoplar daha az gürültüye maruz kalabilir; ATR yüksekken aynı stop mesafesi gereğinden sık çalışabilir.

## Kullanım Örneği

Bir kırılım stratejisinde fiyat EMA 50 üzerinde ve ATR son dönem diplerinden yükseliyorsa, piyasa sıkışmadan çıkıyor olabilir. Bu durumda pozisyon büyüklüğü ATR'ye göre küçültülerek aynı parasal risk korunabilir.

## Tuzaklar ve Riskler

- ATR yön söylemez; yükseliş ya da düşüş sinyali değildir.
- Haber boşlukları ATR'yi bir süre şişirebilir.
- Sabit yüzde stop, ATR rejimi değiştiğinde fazla dar veya fazla geniş kalabilir.
- Çok kısa ATR periyodu gürültüye, çok uzun periyot ise gecikmeye duyarlıdır.

## PiyasaPilot'ta Kullan

Grafikte ATR alt panelini açarak volatilite rejimini izleyebilirsin. Backtest tarafında `supertrend`, ATR tabanlı stop ve yön dönüşü fikrini test etmek için hazır bir başlangıçtır.

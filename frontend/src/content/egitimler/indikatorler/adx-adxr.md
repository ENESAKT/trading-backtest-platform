---
title: ADX / ADXR — Yön Hareketi
slug: adx-adxr
category: indikatorler
tags: [trend, yön, güç, filtre, adx]
difficulty: orta
indicator_key: ADX, ADXR
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, yon_gostermeme, esik_overfit]
copy_policy: original_piyasapilot_content
---

ADX, trendin yönünden çok gücünü okumak için kullanılır. Fiyat yukarı ya da aşağı gidiyor olabilir; ADX'in görevi bu hareketin belirginleşip belirginleşmediğini ayrı bir pencereden göstermektir.

## Nedir?

Yön hareketi ailesinde artı ve eksi yön çizgileri yön tarafını, ADX ise trend gücünü anlatır. ADXR, ADX'in daha yumuşak bir akrabası gibi düşünülebilir; hızlı oynamaları azaltır ama daha geç tepki verir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de ana seriler:

```text
PLUS_DI(14)
MINUS_DI(14)
ADX(14)
ADXR(14,14)
```

Trend filtresi örneği:

```text
C > EMA(C,50) AND PLUS_DI(14) > MINUS_DI(14) AND ADX(14) > 20
```

Bu kural fiyat yönünü EMA ile, yön hareketini DI çizgileriyle, trend gücünü ADX ile kontrol eder.

## Nasıl Okunur?

ADX yükseliyorsa piyasa daha trendli davranıyor olabilir. Düşen ADX, yönlü hareketin zayıfladığını veya piyasanın yataya döndüğünü gösterebilir. ADX yön söylemediği için fiyat yapısı ve DI ilişkisiyle birlikte okunmalıdır.

## Kullanım Örneği

Bir kırılım stratejisinde fiyat direnç üstüne çıkar ama ADX zayıf kalırsa hareketin devam gücü sınırlı olabilir. ADX yükselirken artı yön çizgisi eksi yön çizgisinin üzerindeyse, long senaryonun trend desteği artar.

## Tuzaklar ve Riskler

- ADX yüksek diye yönün yukarı olduğu varsayılmaz.
- ADX gecikmelidir; trend başladıktan sonra güçlenir.
- Sabit eşikler her sembol ve zaman diliminde aynı çalışmaz.
- ADXR daha sakin okuma verir ama ani dönüşlerde geç kalabilir.

## PiyasaPilot'ta Kullan

Bu makalede doğrudan grafik köprüsü yok. Backtest tarafında ADX'i bağımsız giriş sinyali yerine trend filtresi gibi kullanmak daha sağlıklıdır: önce fiyat kuralı, sonra ADX ile piyasa rejimi kontrolü.

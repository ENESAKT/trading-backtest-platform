---
title: Heiken Ashi
slug: heiken-ashi
category: indikatorler
tags: [mum, trend, filtre, gürültü]
difficulty: orta
indicator_key: HA
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, fiyat_gercegi, stop_yanilmasi]
copy_policy: original_piyasapilot_content
---

Heiken Ashi, klasik mumları yumuşatılmış bir fiyat serisine dönüştürerek trend yönünü daha okunur göstermeye çalışır. Bu görünüm gürültüyü azaltır, fakat gerçek açılış-kapanış fiyatlarını birebir temsil etmez.

## Nedir?

Heiken Ashi mumları, fiyatın ortalama davranışını öne çıkarır. Arka arkaya aynı renk mumlar trendin sürdüğünü düşündürebilir; gövde küçülmesi veya fitillerin artması momentum kaybına işaret edebilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de kavramsal seri:

```text
HA_OPEN(O,H,L,C)
HA_HIGH(O,H,L,C)
HA_LOW(O,H,L,C)
HA_CLOSE(O,H,L,C)
```

Trend filtresi:

```text
HA_CLOSE(O,H,L,C) > HA_OPEN(O,H,L,C) AND C > EMA(C,50)
```

## Nasıl Okunur?

Güçlü yükselişte Heiken Ashi mumları daha tutarlı pozitif görünüm verebilir. Gövde küçülüp alt fitiller belirginleşirse trend zayıflıyor olabilir. Yine de işlem fiyatı gerçek mum kapanışına göre planlanmalıdır.

## Kullanım Örneği

Fiyat EMA 50 üzerinde kalırken Heiken Ashi pozitif serisi devam ediyorsa trend takip pozisyonu korunabilir. İlk zayıflama mumunda çıkmak yerine ATR, destek veya klasik kapanış filtresiyle teyit aramak daha kontrollüdür.

## Tuzaklar ve Riskler

- Heiken Ashi gerçek kapanış fiyatı değildir.
- Stop ve emir seviyeleri klasik OHLC verisine göre kurulmalıdır.
- Yumuşatma gecikme yaratır; dönüşler geç fark edilebilir.
- Sadece mum rengine bakmak yatay piyasada yanıltıcıdır.

## PiyasaPilot'ta Kullan

Bu sürümde doğrudan grafik köprüsü yok. PiyasaPilot'ta Heiken Ashi'yi trend görünümü filtresi olarak kullanıp karar seviyelerini gerçek fiyat mumlarıyla doğrulamak gerekir.

---
title: ZigZag
slug: zigzag
category: indikatorler
tags: [trend, swing, formasyon, repaint]
difficulty: orta
indicator_key: ZIGZAG
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [repaint_riski, gecikme, geriye_donuk_yanilgi]
copy_policy: original_piyasapilot_content
---

ZigZag, küçük dalgalanmaları filtreleyip belirgin tepe ve dipleri çizgiyle bağlayan bir görselleştirme aracıdır. Trend, swing ve formasyon çalışmasında faydalıdır; ancak canlı sinyal üretirken dikkat ister.

## Nedir?

ZigZag belirli bir eşikten küçük hareketleri yok sayar. Böylece grafikte ana dalgalar daha temiz görünür. Bu temizlik, çoğu zaman son oluşan tepe veya dip kesinleşmeden değişebildiği için repaint riskini beraberinde getirir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de kavramsal gösterim:

```text
ZIGZAG(C,5)
```

Swing filtresi:

```text
LAST_SWING_HIGH(ZIGZAG(C,5)) > REF(LAST_SWING_HIGH(ZIGZAG(C,5)),1)
```

Bu tür ifadeler geçmiş swing yapısını okumak için yararlıdır; canlı emir tetikleyicisi olarak dikkatle kullanılmalıdır.

## Nasıl Okunur?

Yükselen dipler ve yükselen tepeler trendin yukarı olduğunu, alçalan dipler ve tepeler düşüş eğilimini gösterir. ZigZag, destek-direnç ve formasyon çizimini sadeleştirir ama sinyalin kesinleşme zamanını geciktirir.

## Kullanım Örneği

Fiyat yükselen dipler üretirken son düzeltme önceki ana dip üzerinde kalırsa trend devamı senaryosu kurulabilir. ZigZag bu yapıyı görsel olarak temizler; giriş için yine kapanış, hacim veya momentum teyidi gerekir.

## Tuzaklar ve Riskler

- Son ZigZag noktası yeni fiyatla değişebilir.
- Geçmiş grafikte kusursuz görünen dönüşler canlıda aynı netlikte oluşmaz.
- Eşik çok küçükse gürültü, çok büyükse aşırı gecikme üretir.
- Backtest'te lookahead hatasına çok açıktır.

## PiyasaPilot'ta Kullan

Doğrudan grafik köprüsü yok. PiyasaPilot'ta ZigZag'ı otomatik al-sat sinyali değil, swing yapısını etiketleyen analiz yardımcısı olarak kullanmak daha güvenlidir.

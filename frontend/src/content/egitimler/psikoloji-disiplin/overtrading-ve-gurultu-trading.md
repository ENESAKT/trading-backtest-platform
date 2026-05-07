---
title: Overtrading ve Gürültü Trading
slug: overtrading-ve-gurultu-trading
category: psikoloji-disiplin
tags: [overtrading, gurultu, islem-sikligi, haber, disiplin]
difficulty: orta
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [asiri_islem, komisyon_erozyonu, haber_gurultusu, dikkat_dagilmasi]
copy_policy: original_piyasapilot_content
---

Overtrading, fırsat sayısının artması değil, gereksiz işlem sayısının artmasıdır. Gürültü trading ise her fiyat kıpırdanmasını, her başlığı veya her sosyal sinyali işlem gerekçesi sanma eğilimidir.

## Nedir?

Sağlıklı işlem sıklığı stratejinin ürettiği sinyallerle sınırlıdır. Overtrading başladığında kullanıcı plan dışı sinyaller üretir, pozisyon kapandıktan hemen sonra yeni gerekçe arar ve maliyetler performansı sessizce aşındırır.

## Nasıl Ölçülür?

PiyasaPilot davranış filtresi işlem yoğunluğunu kuralla karşılaştırabilir:

```text
expected_trades = strategy_signal_count
extra_trades = actual_trades - expected_trades
noise_ratio = extra_trades / max(actual_trades, 1)
```

Bu oran yükseliyorsa sorun stratejiden çok kullanıcı müdahalesi olabilir.

## Nasıl Okunur?

İşlem sayısı tek başına kötü değildir; scalping ve kısa vadeli sistemler doğal olarak sık işlem yapabilir. Sorun, işlem sayısının test edilen kuralla açıklanamaması, haber akışıyla plansız artması veya kayıp sonrası hızlanmasıdır.

## Kullanım Örneği

Bir strateji haftada iki sinyal üretirken kullanıcı aynı hafta on iki paper işlem açar. Backtest ile paper sonuçları ayrışır. Journal incelendiğinde sekiz işlemin "haber", "sıkıldım", "kaçırıyorum" gibi plan dışı etiketlerle açıldığı görülür.

## Tuzaklar ve Riskler

- Çok ekran izlemek daha iyi karar anlamına gelmez.
- Sık işlem komisyon ve slipaj etkisini büyütür.
- Kayıp sonrası hemen işlem açmak revenge trade döngüsü yaratabilir.
- Gürültü sinyalleri kısa vadede kazandırsa bile süreç kalitesini bozabilir.

## PiyasaPilot'ta Kullan

Bu makale, ileride işlem sıklığı freni ve journal etiketleriyle güçlendirilecek bir risk kontrolüdür. Şimdilik kullanıcının paper işlemlerinde kural dışı işlem sayısını elle işaretlemesi önerilir.

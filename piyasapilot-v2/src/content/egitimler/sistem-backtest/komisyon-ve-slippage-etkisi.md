---
title: Komisyon ve Slippage Etkisi
slug: komisyon-ve-slippage-etkisi
category: sistem-backtest
tags: [komisyon, slippage, maliyet, likidite]
difficulty: orta
related_strategies: []
source_courses: [kivanc_algo_trade, fuat_sistem_trading]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [maliyet_eksigi, hacimsiz_tahta, aktif_emir_kaymasi]
copy_policy: original_piyasapilot_content
---

Komisyon ve slippage, backtest raporunu canlı piyasa gerçeğine yaklaştıran iki temel maliyettir. Bir strateji küçük fiyat farklarından para kazanmaya çalışıyorsa, bu maliyetler toplam getiriyi tamamen değiştirebilir.

## Komisyon

Komisyon, her işlemde ödenen doğrudan maliyettir. İşlem sayısı arttıkça etkisi büyür. Özellikle kısa vadeli ve sık işlem yapan stratejilerde toplam getiri kadar işlem başına ortalama getiri de izlenmelidir.

## Slippage

Slippage, beklenen fiyat ile gerçekleşen fiyat arasındaki farktır. Aktif emir, düşük derinlik, hızlı piyasa ve hacimsiz tahta bu farkı büyütebilir. Backtestte kapanıştan işlem varsaymak çoğu zaman fazla iyimserdir.

## PiyasaPilot Varsayımı

Backtest sonucunu okurken komisyon, slipaj, işlem yönü ve pozisyon büyüklüğü açık görünmelidir. Varsayım yoksa rapor karar raporu değil, ham simülasyon sayılır.

## Kontrol Listesi

- Komisyon her giriş ve çıkışa uygulanıyor mu?
- Slippage sabit bps, kademe veya hacim oranıyla modellenmiş mi?
- İşlem tutarı sembol hacmine göre makul mü?
- Kısa vadeli stratejide maliyet sonrası kâr hâlâ pozitif mi?
- Açılış/kapanış fill modeli açıkça yazıyor mu?

## Kullanım Örneği

Günde çok sayıda işlem yapan bir momentum stratejisi komisyonsuz testte iyi görünebilir. Her işlemde küçük bir maliyet ve bir kademe kayma eklendiğinde aynı strateji zarar eden yapıya dönüşebilir.

## Tuzaklar ve Riskler

- Maliyetsiz backtest gerçekçi değildir.
- Hacimsiz tahtada teorik fiyatla işlem yapılmış gibi varsaymak yanıltıcıdır.
- Sadece toplam komisyona bakıp kayma etkisini yok saymak hatalıdır.
- Büyük pozisyonlar geçmiş hacimde fark edilmeden fill edilmiş gibi görünebilir.

## PiyasaPilot'ta Kullan

Backtest gerçekçilik fazında komisyon, slipaj ve likidite varsayımları raporun zorunlu parçası olacaktır. Bu kontroller yokken paper veya canlı işlem kararı verilmemelidir.

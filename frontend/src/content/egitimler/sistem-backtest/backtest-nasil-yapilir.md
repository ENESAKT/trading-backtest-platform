---
title: Backtest Nasıl Yapılır?
slug: backtest-nasil-yapilir
category: sistem-backtest
tags: [backtest, test, varsayim, rapor]
difficulty: orta
related_strategies: [sma_crossover]
source_courses: [kivanc_algo_trade, fuat_sistem_trading]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecmis_veri_yanilgisi, maliyet_eksigi, yetersiz_orneklem]
copy_policy: original_piyasapilot_content
---

Backtest, bir strateji kuralının geçmiş veride nasıl davranmış olabileceğini ölçer. Doğru yapıldığında sistemi elemek için güçlü bir filtredir; yanlış yapıldığında yalnızca güzel görünen ama canlı piyasada kırılgan bir rapor üretir.

## Nedir?

Backtest, giriş-çıkış kurallarını belirli sembol, zaman aralığı, sermaye ve maliyet varsayımlarıyla çalıştırır. Sonuç; getiri, işlem sayısı, düşüş, komisyon ve işlem dağılımı gibi metriklerle değerlendirilir.

## PiyasaPilot Akışı

Önce strateji fikri seçilir. Sonra sembol, timeframe, test aralığı, sermaye, komisyon ve pozisyon büyüklüğü belirlenir. Test bitince tek başına toplam getiriye değil, işlem kalitesi ve risk dağılımına bakılır.

## Kontrol Listesi

- Test aralığı strateji vadesine uygun mu?
- Yeterli bar ve yeterli işlem var mı?
- Komisyon ve slipaj varsayımı açık mı?
- Sembol seçimi önyargı üretmiyor mu?
- Sonuçlar farklı piyasa koşullarında da okunuyor mu?

## Kullanım Örneği

SMA kesişim stratejisini yalnızca güçlü yükselmiş bir hissede test etmek yanıltıcıdır. Aynı kuralı yatay dönem, düşüş dönemi ve farklı sembollerde çalıştırmak, sistemin ne zaman işe yaradığını ve ne zaman zarar ürettiğini gösterir.

## Tuzaklar ve Riskler

- Geçmiş veri gelecek davranışı garanti etmez.
- En iyi sembolü seçip raporu genellemek önyargıdır.
- Komisyon ve slipaj kapalıyken kısa vadeli sistemler olduğundan iyi görünür.
- Intrabar high/low bilgisiyle gerçek dışı fill varsayımı oluşabilir.

## PiyasaPilot'ta Kullan

`sma_crossover` preset'iyle basit bir backtest başlatıp raporda işlem sayısı, getiri ve risk uyarılarını izleyebilirsin. Ağır doğrulama adımları WFA ve Monte Carlo fazlarında eklenecektir.

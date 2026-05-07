---
title: Monte Carlo Simülasyonu
slug: monte-carlo-simulasyonu
category: sistem-backtest
tags: [monte-carlo, risk, dagilim, drawdown]
difficulty: ileri
related_strategies: []
source_courses: [kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [dagilim_yanilgisi, az_islem, kotu_senaryo]
copy_policy: original_piyasapilot_content
---

Monte Carlo simülasyonu, tek bir backtest sermaye eğrisine bakmak yerine işlem sonuçlarının farklı sıralarda ve örneklerde nasıl risk üretebileceğini görmeye yarar. En iyi senaryoyu değil, dayanıklılığı sorgular.

## Nedir?

Backtest bir işlem listesi üretir. Monte Carlo bu listeyi yeniden örnekleyerek çok sayıda olası yol oluşturur. Böylece medyan sonuç, kötü senaryo, zarar olasılığı ve beklenenden büyük drawdown ihtimali okunabilir.

## Neden Gerekli?

İki strateji aynı toplam getiriyi üretse bile risk dağılımları farklı olabilir. Biri istikrarlı küçük kazançlarla ilerlerken diğeri az sayıda büyük işlemle sonucu taşımış olabilir. Monte Carlo bu kırılganlığı görünür yapar.

## Kontrol Listesi

- İşlem sayısı simülasyon için yeterli mi?
- PnL dağılımında tek bir aşırı kazanç sonucu domine ediyor mu?
- Kötü senaryoda maksimum düşüş kabul edilebilir mi?
- Zarar etme olasılığı karar eşiğinin altında mı?
- Sabit seed ile tekrar üretilebilir rapor alınıyor mu?

## Kullanım Örneği

Backtest yüzde 40 getiri göstermiş olabilir. Monte Carlo sonucunda kötü yüzde 5 senaryoda sermaye eğrisi derin düşüşe giriyorsa, sistem kârlı görünse bile pozisyon büyüklüğü veya eleme kararı yeniden düşünülmelidir.

## Tuzaklar ve Riskler

- Az işlemli stratejilerde simülasyon sonucu güvenilir olmayabilir.
- Geçmiş PnL dağılımı gelecek piyasa rejimini tam temsil etmez.
- Monte Carlo kötü sistemi kurtarmaz, yalnızca riskini görünür yapar.
- Sadece medyan sonuca bakmak kuyruk riskini saklar.

## PiyasaPilot'ta Kullan

Monte Carlo, paper robot öncesi son risk kapılarından biri olacak. Rapor, medyan sermaye, kötü senaryo drawdown ve zarar olasılığıyla birlikte okunacaktır.

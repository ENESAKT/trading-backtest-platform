---
title: Algoritmik Trade Nedir?
slug: algoritmik-trade-nedir
category: sistem-backtest
tags: [algoritmik-trade, sistem, kural, otomasyon]
difficulty: başlangıç
related_strategies: [sma_crossover]
source_courses: [kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [otomasyon_yanilgisi, likidite_riski, hedef_belirsizligi]
copy_policy: original_piyasapilot_content
---

Algoritmik trade, piyasa fikrini açık kurallara dönüştürüp bu kuralları test edilebilir hale getirme disiplinidir. Amaç ekrana bakmadan mucize üretmek değil; ne zaman işlem açılacağını, ne zaman çıkılacağını ve hangi durumda sistemin durdurulacağını önceden tanımlamaktır.

## Nedir?

Bir sistemin kalbi trade fikridir. Bu fikir trend takibi, ortalamaya dönüş, momentum, kırılım ya da risk azaltma gibi basit bir gözlemden doğabilir. Fikir, ölçülebilir kurallara çevrilmeden algoritmik sistem sayılmaz.

## PiyasaPilot Bakışı

PiyasaPilot'ta algoritmik trade üç katmanlı düşünülür: fikir, test ve canlıya hazırlık. Fikir kısmında kural açık yazılır. Test kısmında geçmiş veri, komisyon, slipaj ve işlem sayısı kontrol edilir. Canlıya hazırlıkta ise paper izleme, alarm ve risk limiti devreye girer.

## İyi Bir Sistem Soruları

- Hangi piyasa koşulunda çalışması bekleniyor?
- Giriş ve çıkış kuralları net mi?
- Stop, hedef ve pozisyon büyüklüğü tanımlı mı?
- Yeterli işlem örneği üretiyor mu?
- Hacim ve veri kalitesi gerçek işleme uygun mu?

## Kullanım Örneği

Basit hareketli ortalama kesişimi bir algoritmik trade fikridir. Hızlı ortalama yavaş ortalamayı yukarı kesince al, aşağı kesince çık gibi açık bir kural yazılabilir. Sonra bu kural farklı sembol, dönem ve maliyet varsayımlarıyla sınanır.

## Tuzaklar ve Riskler

- Otomasyon kötü fikri iyi sisteme dönüştürmez.
- Çok fazla koşul eklemek geçmişe aşırı uyum yaratabilir.
- Hacimsiz piyasada kâğıt üstündeki sinyal gerçek emirle bozulabilir.
- Canlıya geçmeden paper izleme yapılmaması riski büyütür.

## PiyasaPilot'ta Kullan

Bu makaleden `sma_crossover` preset'ine geçerek kural, parametre ve backtest akışını görebilirsin. Daha ileri sistemler için aynı fikir StrategySpec tarafında çoğaltılacaktır.

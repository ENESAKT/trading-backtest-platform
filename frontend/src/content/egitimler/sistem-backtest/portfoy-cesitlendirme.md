---
title: Portföy Çeşitlendirme
slug: portfoy-cesitlendirme
category: sistem-backtest
tags: [portfoy, cesitlendirme, korelasyon, risk-butcesi]
difficulty: ileri
related_strategies: []
source_courses: [kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [sahte_cesitlendirme, korelasyon_riski, toplam_risk]
copy_policy: original_piyasapilot_content
---

Portföy çeşitlendirme, tek bir stratejinin iyi görünmesine güvenmek yerine farklı strateji, sembol ve zaman dilimlerinin birlikte nasıl risk ürettiğini ölçer. Amaç çok şey çalıştırmak değil, aynı anda aynı hatayı yapmayan sistemler kurmaktır.

## Nedir?

Gerçek çeşitlendirme, birbirinden bağımsız davranan getiri kaynaklarıyla oluşur. Aynı indikatör ailesinin aynı sembollerde farklı parametrelerle çalışması çoğu zaman çeşitlendirme değil, aynı riskin çoğaltılmasıdır.

## PiyasaPilot Bakışı

Portföy Lab, strateji başına değil, toplam sermaye eğrisi üzerinden düşünmelidir. Korelasyon, toplam drawdown, strateji başına risk bütçesi ve aynı anda açık pozisyon yoğunluğu birlikte izlenir.

## Kontrol Listesi

- Stratejiler farklı piyasa rejimlerinden mi kazanç bekliyor?
- Semboller yüksek korelasyonlu mu?
- Aynı anda zarar yazan sistem sayısı izleniyor mu?
- Her stratejinin sermaye payı sınırlı mı?
- Pasif benchmark ile karşılaştırma yapılıyor mu?

## Kullanım Örneği

Trend takip stratejisi yükselen piyasada güçlü olabilir, mean reversion ise yatay dönemde daha dengeli çalışabilir. Bu iki sistemin birleşik sermaye eğrisi, tek tek sonuçlardan daha anlamlı bir karar zemini sunar.

## Tuzaklar ve Riskler

- Çok sayıda benzer strateji toplam riski azaltmaz.
- Korelasyon kriz dönemlerinde artabilir.
- En iyi stratejiye aşırı sermaye ayırmak portföy disiplinini bozar.
- Sadece getiriye bakıp en kötü dönemleri yok saymak yanıltıcıdır.

## PiyasaPilot'ta Kullan

Portföy Lab fazında birden çok strateji ve sembolün birleşik equity curve'ü, korelasyon matrisi ve toplam risk uyarıları üretilecek. Bu makale o karar çerçevesinin temelidir.

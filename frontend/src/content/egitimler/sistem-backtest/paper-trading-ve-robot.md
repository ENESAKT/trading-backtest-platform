---
title: Paper Trading ve Robot
slug: paper-trading-ve-robot
category: sistem-backtest
tags: [paper-trading, robot, alarm, risk-limiti]
difficulty: orta
related_strategies: []
source_courses: [kivanc_algo_trade, fuat_sistem_trading]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [canli_islem_riski, otomatik_emir_yanilgisi, kill_switch_eksigi]
copy_policy: original_piyasapilot_content
---

Paper trading, stratejiyi gerçek para riske etmeden canlı akışa yakın bir ortamda izleme aşamasıdır. Robot ise kuralları otomatik takip eden yapı anlamına gelir; PiyasaPilot'ta alarm, paper işlem ve gerçek emir kavramları bilinçli biçimde ayrılır.

## Nedir?

Backtest geçmişi, paper trading bugünü sınar. Paper aşamasında stratejinin sinyal üretimi, varsayımlar, gecikme, veri kalitesi ve kullanıcı davranışı gözlenir. Robot fikri ancak bu aşama sağlıklıysa anlam kazanır.

## PiyasaPilot Kapıları

Bir strateji paper izlemeye alınmadan önce veri yeterliliği, maliyet varsayımı, WFA/Monte Carlo sonucu ve risk limitleri kontrol edilmelidir. Kill switch ve günlük zarar limiti yoksa otomasyon eksik sayılır.

## Kontrol Listesi

- Strateji neden işlem açtığını açıklayabiliyor mu?
- Alarm üretmek ile paper pozisyon açmak ayrılmış mı?
- Günlük zarar ve toplam drawdown limiti var mı?
- Veri kesilirse robot durumu güvenli mi?
- Paper sonuçları backtest varsayımlarıyla karşılaştırılıyor mu?

## Kullanım Örneği

Bir RSI stratejisi backtestte kabul edilebilir görünür. Paper aşamasında sinyal geldiğinde sanal pozisyon açılır, PnL ve işlem gerekçesi kaydedilir. Beklenen fill ile simüle edilen fill sürekli ayrışıyorsa canlıya geçiş ertelenir.

## Tuzaklar ve Riskler

- Paper kârı gerçek emir başarısı anlamına gelmez.
- Otomatik emir güvenlik kapıları olmadan çalıştırılmamalıdır.
- Veri gecikmesi veya kopması sinyal kalitesini bozabilir.
- Kullanıcı stratejiyi paper aşamasında sürekli değiştirirse ölçüm bozulur.

## PiyasaPilot'ta Kullan

PiyasaPilot şu aşamada gerçek emir kapsamını dışarıda tutar. Paper robotlar analiz, alarm ve sanal portföy disiplini için kullanılacak; canlı emir kararı ayrı ve kapılı bir ürün alanı olarak kalacaktır.

---
title: Kayıp Serisi Yönetimi
slug: kayip-serisi-yonetimi
category: psikoloji-disiplin
tags: [kayip-serisi, drawdown, mola, risk-freni, psikoloji]
difficulty: orta
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: medium
needs_audio_transcript: true
risk_warnings: [revenge_trade, pozisyon_buyutme, drawdown, psikolojik_yorgunluk]
copy_policy: original_piyasapilot_content
---

Kayıp serisi, yalnız sermayeyi değil karar kalitesini de yorar. Üst üste gelen zararlar kullanıcıyı ya tamamen pasifleştirir ya da kaybı hızlı geri alma isteğiyle plan dışı işlem açmaya iter.

## Nedir?

Kayıp serisi yönetimi, arka arkaya gelen zararların strateji sınırları içinde mi yoksa süreç bozulması nedeniyle mi oluştuğunu ayırır. Bu ayrım yapılmadan pozisyon büyütmek, parametre değiştirmek veya stratejiyi terk etmek sağlıklı değildir.

## Nasıl Ölçülür?

PiyasaPilot risk freni şu alanları izleyebilir:

```text
loss_streak = COUNT_CONSECUTIVE(losing_trades)
daily_loss_limit_hit = realized_loss_today <= -daily_limit
pause_required = loss_streak >= max_loss_streak OR daily_loss_limit_hit
```

Bu kural ceza değil, karar kalitesini koruyan mola mekanizmasıdır.

## Nasıl Okunur?

Her stratejinin doğal kayıp serisi olabilir. Backtestte görülen en kötü seri ile paper aşamasındaki seri karşılaştırılmalıdır. Paper kayıp serisi backtest sınırını aşıyorsa piyasa rejimi değişmiş, veri kalitesi bozulmuş veya kullanıcı plana müdahale etmiş olabilir.

## Kullanım Örneği

Bir momentum sistemi geçmiş testte en fazla dört ardışık kayıp üretmiştir. Paper aşamasında altı kayıp üst üste gelirse sistem otomatik olarak "mola ve inceleme" durumuna alınır. Kullanıcı yeni işlem açmadan önce son işlemlerin kural uyumunu kontrol eder.

## Tuzaklar ve Riskler

- Kayıp sonrası pozisyon büyütmek riski hızla artırır.
- Her kayıp serisi stratejinin bittiği anlamına gelmez.
- Sınırları işlem sırasında değiştirmek risk frenini anlamsızlaştırır.
- Sadece psikolojiye odaklanıp piyasa rejimi değişimini atlamamak gerekir.

## PiyasaPilot'ta Kullan

Bu makale ileride kayıp serisi mola kuralına bağlanacak. Şimdilik paper raporunda ardışık kayıp, günlük zarar limiti ve plan dışı müdahale notları birlikte izlenmelidir.

---
title: Hedge, Spekülatif ve Arbitraj
slug: hedge-spekulatif-ve-arbitraj
category: viop-vadeli
tags: [hedge, spekulasyon, arbitraj, risk-yonetimi, viop]
difficulty: orta
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [hedge_uyumsuzlugu, kaldirac_riski, maliyet_riski, likidite_riski]
copy_policy: original_piyasapilot_content
---

Vadeli piyasada aynı araç farklı amaçlarla kullanılabilir: riskten korunma, yön beklentisi veya fiyat farkı değerlendirme. PiyasaPilot'ta bu amaçlar aynı grafikte görünse bile raporda ayrı etiketlenmelidir.

## Nedir?

Hedge, mevcut riskin bir bölümünü azaltmayı hedefler. Spekülatif işlem, fiyat yönünden getiri arar. Arbitraj ise ilişkili piyasalardaki fiyat farkının maliyetlerden sonra kapanacağı varsayımına dayanır.

## Nasıl Sınıflanır?

Eğitim amaçlı sınıflama:

```text
intent = "hedge" | "directional" | "spread_arbitrage"
risk_source = "existing_position" | "new_exposure" | "relative_price_gap"
```

Bu ayrım stratejinin performansını değil, hangi riski taşıdığını ve neye karşı ölçülmesi gerektiğini belirler.

## Nasıl Okunur?

Hedge işleminde başarı, tek başına vadeli pozisyon karı değildir; korunmak istenen spot riskle birlikte değerlendirilir. Spekülatif işlemde kaldıraç ve stop disiplini öne çıkar. Arbitrajda ise işlem maliyeti, likidite, teminat ve zamanlama riski farkı hızla silebilir.

## Kullanım Örneği

Spot portföyü yüksek olan bir kullanıcı düşüş riskini azaltmak için endeks vadeli kısa pozisyon düşünebilir. Bu işlem tek başına zarar yazsa bile spot portföyü koruyorsa amacına yaklaşmış olabilir. Aynı kısa pozisyon yön tahminiyle açıldıysa başarı ölçütü tamamen değişir.

## Tuzaklar ve Riskler

- Hedge oranı yanlışsa koruma eksik veya aşırı olabilir.
- Spekülatif pozisyon hedge gibi adlandırılırsa risk büyüklüğü gizlenir.
- Arbitraj gibi görünen fark maliyet ve teminat sonrası fırsat olmayabilir.
- Spot portföy ile vadeli dayanak tam örtüşmüyorsa baz riski oluşur.

## PiyasaPilot'ta Kullan

Bu makalede aktif strateji köprüsü yoktur. Gelecek VIOP Lab için işlem amacı alanı zorunlu olmalıdır; hedge, spekülatif ve arbitraj etiketleri aynı rapor metriğiyle değerlendirilmemelidir.

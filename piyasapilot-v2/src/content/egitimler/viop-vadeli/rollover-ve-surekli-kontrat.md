---
title: Rollover ve Sürekli Kontrat
slug: rollover-ve-surekli-kontrat
category: viop-vadeli
tags: [rollover, surekli-kontrat, vade-gecisi, viop, backtest]
difficulty: ileri
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [vade_gecisi, fiyat_bosluklari, geriye_donuk_duzeltme, likidite_kaymasi]
copy_policy: original_piyasapilot_content
---

Rollover, vadesi yaklaşan kontrattaki pozisyonu yeni vadeye taşıma sürecidir. Sürekli kontrat ise farklı vadeleri tek zaman serisi gibi analiz etmek için kurulan sentetik grafiktir.

## Nedir?

Vadeli kontratlar sınırsız yaşamaz; her kontratın bir vadesi vardır. Uzun dönem analiz yapmak isteyen kullanıcı, eski kontrattan yeni kontrata hangi tarihte ve hangi fiyat mantığıyla geçileceğini tanımlamak zorundadır.

## Nasıl Hesaplanır?

PiyasaPilot'ta rollover kuralı açık bir seçim olarak tutulmalıdır:

```text
ROLLOVER(
  from: "near_expiry",
  to: "next_expiry",
  rule: "volume_lead" | "days_before_expiry" | "manual",
  adjustment: "none" | "difference" | "ratio"
)
```

Bu ayarlar olmadan sürekli kontrat grafiği sadece görsel kolaylık sağlar; test kanıtı sayılmamalıdır.

## Nasıl Okunur?

Vade geçişinde iki kontrat arasında fiyat farkı olabilir. Bu fark gerçek piyasa fırsatı değil, vade yapısının sonucu olabilir. Sürekli kontrat düzeltilmişse geçmiş fiyatlar değişmiş gibi görünür; düzeltilmemişse grafikte yapay boşluklar oluşabilir.

## Kullanım Örneği

Bir hareketli ortalama sistemi yıl boyunca endeks vadeli kontratta denenir. Yakın vade bittiğinde sistem yeni vadeye geçtiği günü bilmiyorsa, sinyalin bir kısmı fiyat boşluğundan kaynaklanabilir. Bu nedenle rollover günü ve düzeltme yöntemi raporda görünmelidir.

## Tuzaklar ve Riskler

- Eski ve yeni vadeyi düz bağlamak yapay kar/zarar üretebilir.
- Geriye dönük düzeltme fiyat seviyesini değiştirir; stop ve hedef yorumunu etkiler.
- Likidite yeni vadeye geçmeden önce taşınmak gerçekçi olmayabilir.
- Manuel rollover kuralı raporda saklanmazsa sonuç tekrar üretilemez.

## PiyasaPilot'ta Kullan

Bu aşamada VIOP sürekli kontrat üretimi kapalıdır. Makale, ileride eklenecek VIOP Lab için zorunlu rapor alanlarını belirler: rollover kuralı, geçiş tarihi, düzeltme yöntemi ve likidite kontrolü.

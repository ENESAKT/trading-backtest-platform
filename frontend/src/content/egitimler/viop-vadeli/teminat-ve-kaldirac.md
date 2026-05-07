---
title: Teminat ve Kaldıraç
slug: teminat-ve-kaldirac
category: viop-vadeli
tags: [teminat, kaldirac, risk, pozisyon, viop]
difficulty: orta
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [kaldirac_riski, teminat_tamamlama, zorunlu_pozisyon_kapatma, nakit_yonetimi]
copy_policy: original_piyasapilot_content
---

Teminat, vadeli pozisyonun tamamını ödemek yerine belirli bir güvenceyle pozisyon açmayı sağlar. Bu yapı sermaye verimliliği sunsa da aynı anda kaldıraç etkisi yarattığı için risk hesabının merkezinde durur.

## Nedir?

Başlangıç teminatı pozisyon açarken ayrılan tutardır. Sürdürme eşiği ise pozisyon açıkken teminat seviyesinin izlenmesi gereken alt bölgeyi temsil eder. Fiyat ters hareket ettiğinde ek teminat gereksinimi doğabilir.

## Nasıl Hesaplanır?

PiyasaPilot raporunda teminat etkisi ayrı bir varsayım olarak tutulmalıdır:

```text
notional_value = contract_price * contract_multiplier * quantity
effective_leverage = notional_value / allocated_margin
```

Bu gösterim eğitim amaçlıdır; gerçek teminat oranları piyasa, kurum ve dönem bazında değişebilir.

## Nasıl Okunur?

Kaldıraç, yön doğruyken getiriyi büyüttüğü gibi yön tersken kaybı da büyütür. Bu yüzden vadeli raporda yalnızca yüzde getiri değil, teminat kullanımı, maksimum ters hareket, nakit tamponu ve pozisyon kapatma riski birlikte okunmalıdır.

## Kullanım Örneği

Bir trend sistemi endeks vadelide karlı görünebilir. Fakat aynı sistemin en kötü kayıp serisi teminat tamponunu tüketiyorsa, rapor pratikte sürdürülebilir değildir. Daha düşük kontrat adedi, daha geniş nakit tamponu veya işlem sıklığı filtresi gerekebilir.

## Tuzaklar ve Riskler

- Düşük teminatla yüksek pozisyon açmak ani teminat çağrısı doğurabilir.
- Sadece başlangıç teminatına bakmak, açık pozisyon riskini hafife aldırır.
- Backtestte teminat çağrısı modellenmezse strateji olduğundan dayanıklı görünür.
- Gün içi sert hareketler kapanış bazlı raporda saklanabilir.

## PiyasaPilot'ta Kullan

Bu makalede aktif strateji köprüsü yoktur. VIOP modülü açılmadan önce raporun teminat varsayımını, nakit tamponunu ve kaldıraç sınırını açıkça göstermesi gerekir.

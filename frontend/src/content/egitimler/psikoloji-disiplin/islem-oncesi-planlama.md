---
title: İşlem Öncesi Planlama
slug: islem-oncesi-planlama
category: psikoloji-disiplin
tags: [planlama, risk, vade, hedef, checklist]
difficulty: orta
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [plansiz_islem, vade_uyumsuzlugu, hedef_stop_eksigi, sermaye_riski]
copy_policy: original_piyasapilot_content
---

İşlem öncesi planlama, sinyal geldikten sonra değil, sinyal gelmeden önce yapılır. Çünkü fiyat hareketi başladıktan sonra karar sistemi çoğu zaman hedef, stop ve vade yerine korku ve kaçırma hissiyle çalışır.

## Nedir?

İşlem planı; neden giriş yapılacağını, hangi koşulda vazgeçileceğini, ne kadar risk alınacağını, hedefin ne olduğunu ve işlemin hangi vadede değerlendirileceğini yazar. Plan yoksa işlem sonucu ölçülemez; yalnızca tahminin tuttuğu veya tutmadığı görülür.

## Nasıl Ölçülür?

PiyasaPilot checklist'i basit bir kilit mantığıyla çalışabilir:

```text
can_open_trade =
  has_entry_reason AND
  has_stop AND
  has_target AND
  has_time_horizon AND
  position_size_defined
```

Bu alanlardan biri eksikse işlem paper aşamasında bile "plansız" etiketi almalıdır.

## Nasıl Okunur?

Plan, fiyatın ne yapacağını garanti etmez; kullanıcının ne yapacağını netleştirir. En değerli planlar kısa, ölçülebilir ve işlem sırasında değiştirilemeyecek kadar nettir. Girişten sonra hedef veya stop sürekli değişiyorsa plan karar desteği olmaktan çıkar.

## Kullanım Örneği

Kullanıcı bir kırılım gördüğünde önce giriş nedeni, stop seviyesi, hedef bölgesi, beklenen vade ve maksimum pozisyon büyüklüğünü yazar. Fiyat hızla hareket etse bile eksik alan varsa işlem açılmaz. Bu küçük gecikme birçok dürtüsel işlemi engeller.

## Tuzaklar ve Riskler

- Planı sadece işlemden sonra doldurmak geriye dönük gerekçe üretir.
- Hedef yazıp stop yazmamak eksik plandır.
- Vade belirsizse kısa vadeli stres uzun vadeli kararı bozabilir.
- Sermaye ihtiyacı ve likidite düşünülmeden açılan işlem erken kapatmaya zorlayabilir.

## PiyasaPilot'ta Kullan

Bu makale, Eğitimler v1'in en pratik kontrol listesidir. Paper işlem açmadan önce giriş nedeni, stop, hedef, vade ve pozisyon büyüklüğü alanlarının doldurulması ileride zorunlu kapıya dönüştürülebilir.

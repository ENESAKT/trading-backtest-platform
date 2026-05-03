---
title: Kurumsal Aksiyonlar ve Kontrat Uyarlaması
slug: kurumsal-aksiyonlar-ve-kontrat-uyarlamasi
category: viop-vadeli
tags: [kurumsal-aksiyon, temettu, bedelli, bedelsiz, kontrat-uyarlamasi]
difficulty: ileri
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [kurumsal_aksiyon, gecmis_veri_duzeltmesi, kontrat_standardi, model_riski]
copy_policy: original_piyasapilot_content
---

Pay vadeli kontratlarda temettü, bedelli sermaye artırımı, bedelsiz sermaye artırımı veya sermaye azaltımı gibi kurumsal aksiyonlar kontratın ekonomik anlamını değiştirebilir. Bu nedenle grafik ve backtest yalnızca fiyat serisine bakarak yorumlanmamalıdır.

## Nedir?

Kurumsal aksiyon, şirketin sermaye yapısı veya nakit dağıtımıyla ilgili bir olaydır. Bu olaylar spot hisse fiyatını etkileyebilir; vadeli kontratta ise sözleşme büyüklüğü, referans fiyat veya standart kontrat niteliği üzerinde uyarlama gerektirebilir.

## Nasıl Hesaplanır?

PiyasaPilot tarafında olay bir düzeltme kaydı olarak saklanmalıdır:

```text
CORPORATE_ACTION_ADJUSTMENT(
  event_type,
  event_date,
  price_adjustment,
  multiplier_adjustment,
  contract_status
)
```

Gerçek oran ve yöntemler resmi piyasa duyurularına göre değişir; makale yalnızca modelleme ihtiyacını anlatır.

## Nasıl Okunur?

Temettü beklentisi vadeli fiyatı spotla aynı çizgide göstermeyebilir. Bedelli veya bedelsiz süreçler ise geçmiş fiyat, pozisyon değeri ve kontrat standardı açısından ayrı ele alınmalıdır. Uyarlama yoksa eski ve yeni fiyatlar aynı strateji serisinde yanlış bağlanabilir.

## Kullanım Örneği

Bir pay vadeli kontratta temettü takvimi yaklaşırken teorik fiyat farkı değişebilir. Kullanıcı bunu teknik kırılım sanarsa hatalı yorum yapabilir. Raporda olay tarihi ve kontrat uyarlaması görünürse sinyalin piyasa davranışından mı, kurumsal olaydan mı kaynaklandığı daha rahat ayrılır.

## Tuzaklar ve Riskler

- Kurumsal aksiyon günü normal fiyat boşluğu gibi test edilirse yapay sinyal oluşur.
- Kontrat büyüklüğü değiştiği halde pozisyon adedi aynı kabul edilmemelidir.
- Resmi uyarlama duyurusu olmadan geriye dönük fiyat düzeltmesi varsayılmamalıdır.
- Temettü beklentisi teorik fiyatı etkiler; gerçekleşme takvimi ayrıca kontrol edilmelidir.

## PiyasaPilot'ta Kullan

Bu sürümde pay vadeli kontrat uyarlama motoru yoktur. VIOP makalesi, ileride resmi kurumsal aksiyon verisi bağlanmadan pay vadeli backtestlerin sınırlı güvenle etiketlenmesi gerektiğini belirtir.

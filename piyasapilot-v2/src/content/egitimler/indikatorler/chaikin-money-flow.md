---
title: Chaikin Money Flow
slug: chaikin-money-flow
category: indikatorler
tags: [hacim, para akışı, birikim, dağıtım]
difficulty: orta
indicator_key: CMF
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [hacim_verisi, yatay_piyasa, tek_bar_etkisi]
copy_policy: original_piyasapilot_content
---

Chaikin Money Flow, belirli bir dönem boyunca fiyatın gün içi aralığın neresinde kapandığını hacimle birlikte değerlendirir. Pozitif değerler birikim, negatif değerler dağıtım baskısına işaret edebilir.

## Nedir?

CMF, kapanışın bar aralığındaki konumunu hacimle ağırlıklandırır. Fiyat üst bölgelere yakın kapanıp hacim de güçlü kalıyorsa para akışı pozitifleşebilir; alt bölge kapanışları ve hacim ise negatif baskıyı artırabilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri:

```text
CMF(H,L,C,V,21)
```

Kırılım teyidi:

```text
C > HIGHEST(C,20) AND CMF(H,L,C,V,21) > 0
```

Bu kural fiyat kırılımının pozitif para akışıyla desteklenip desteklenmediğini kontrol eder.

## Nasıl Okunur?

Sıfır üstü değerler alıcı tarafının, sıfır altı değerler satıcı tarafının daha aktif olduğunu gösterebilir. CMF kalıcı biçimde pozitifken fiyatın destek üstünde tutunması birikim senaryosunu güçlendirir.

## Kullanım Örneği

Bir hisse direnç üstüne çıkarken CMF sıfır üstünde kalıyorsa kırılım daha sağlıklı görünebilir. Fiyat yükselirken CMF sıfır altına sarkıyorsa hareketin hacim desteği zayıflıyor olabilir.

## Tuzaklar ve Riskler

- Hacim verisi güvenilir değilse CMF yorumlanmamalıdır.
- Tek bir yüksek hacimli bar dönem boyunca etki yaratabilir.
- Sıfır çizgisi çevresindeki küçük dalgalanmalar gürültü olabilir.
- Likiditesi zayıf sembollerde para akışı yorumu hızlı bozulur.

## PiyasaPilot'ta Kullan

Bu konu için doğrudan grafik köprüsü yok. PiyasaPilot'ta CMF'yi kırılım, trend veya destek dönüşü kuralına hacim teyidi ekleyen filtre olarak kullanmak daha sağlıklı olur.

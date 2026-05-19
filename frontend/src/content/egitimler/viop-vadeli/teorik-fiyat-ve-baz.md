---
title: Teorik Fiyat ve Baz
slug: teorik-fiyat-ve-baz
category: viop-vadeli
tags: [teorik-fiyat, baz, tasima-maliyeti, arbitraj, viop]
difficulty: ileri
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [model_riski, faiz_temettu_varsayimi, likidite_riski, arbitraj_yanilgisi]
copy_policy: original_piyasapilot_content
---

Teorik fiyat, vadeli kontratın spot fiyatla ilişkisini faiz, taşıma maliyeti, beklenen nakit akışları ve vadeye kalan süre üzerinden düşünmeye yarar. Baz ise spot ile vadeli fiyat arasındaki farkın risk ve beklenti tarafını görünür kılar.

## Nedir?

Vadeli fiyat her zaman spot fiyatın aynısı olmak zorunda değildir. Piyasa, dayanak varlığı bugünden vadeye taşımanın maliyetini, beklenen temettü veya nakit akışını ve arz-talep dengesini fiyatlayabilir. Baz bu ilişkinin yönünü ve büyüklüğünü izlemek için kullanılır.

## Nasıl Hesaplanır?

PiyasaPilot eğitim diliyle teorik çerçeve şöyle özetlenir:

```text
theoretical_price = spot_effect + carry_effect - expected_cash_flow_effect
basis = futures_price - spot_reference
```

Gerçek piyasa hesabında faiz, gün sayımı, temettü beklentisi ve kontrat özellikleri ayrıca tanımlanmalıdır; burada amaç birebir fiyatlama motoru değil, varsayım farkındalığıdır.

## Nasıl Okunur?

Baz açılıyorsa vadeli fiyat spot referansa göre daha pahalı hale geliyor olabilir. Baz daralıyorsa vade sonuna yaklaşma, beklenti değişimi veya spot-vadeli arbitraj baskısı devrede olabilir. Tek başına "ucuz" veya "pahalı" kararı için yeterli değildir.

## Kullanım Örneği

Endeks vadeli fiyatı spot endeksin belirgin üstünde seyrediyorsa kullanıcı bunu yükseliş sinyali sanabilir. Oysa farkın bir bölümü vadeye kalan süre ve taşıma maliyetiyle açıklanabilir. Strateji, baz hareketini yön sinyalinden ayrı okumalıdır.

## Tuzaklar ve Riskler

- Faiz ve temettü varsayımı yanlışsa teorik değer yanıltır.
- Likidite düşükse baz farkı model değil emir defteri kaynaklı olabilir.
- Arbitraj fırsatı gibi görünen fark, işlem maliyeti ve teminatla kapanabilir.
- Vade sonuna yakın baz davranışı normal dönemle aynı kabul edilmemelidir.

## PiyasaPilot'ta Kullan

Bu sürümde teorik fiyat hesaplayıcısı yoktur. VIOP içeriği, ileride spot-vadeli karşılaştırma eklendiğinde model varsayımlarının raporda açık yazılması gerektiğini belirtir.

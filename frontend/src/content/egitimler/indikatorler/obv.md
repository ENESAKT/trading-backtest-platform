---
title: OBV — On-Balance Volume
slug: obv
category: indikatorler
tags: [hacim, momentum, birikim, dağıtım, teyit]
difficulty: orta
indicator_key: OBV
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [hacim_verisi, uyumsuzluk_yanilmasi, tek_bar_sicramasi]
copy_policy: original_piyasapilot_content
---

OBV, fiyat hareketini hacim akışıyla birlikte okumaya yarayan kümülatif bir göstergedir. Ana fikir basittir: yükselen kapanışlarda hacim pozitif, düşen kapanışlarda hacim negatif tarafta birikir.

## Nedir?

Fiyat yeni zirveye giderken OBV de yükseliyorsa hareket hacimle destekleniyor olabilir. Fiyat yükselirken OBV yatay veya aşağı kalıyorsa, alım ilgisinin zayıfladığına dair erken bir uyarı oluşabilir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri:

```text
OBV(C,V)
```

Teyit filtresi örneği:

```text
C > HIGHEST(C,20) AND OBV(C,V) > HIGHEST(OBV(C,V),20)
```

Bu kural fiyat kırılımının hacim birikimiyle desteklenip desteklenmediğini kontrol eder.

## Nasıl Okunur?

OBV'nin yönü, fiyatın arkasındaki katılımı okumaya yardım eder. Fiyat yatayken OBV yükseliyorsa sessiz bir birikim, fiyat yükselirken OBV düşüyorsa zayıf katılım ihtimali değerlendirilebilir.

## Kullanım Örneği

Bir hisse dar banttan yukarı çıkarken OBV de son 20 barın zirvesini geçiyorsa, kırılım yalnızca fiyat hareketi değildir; hacim tarafında da katılım vardır. Fiyat kırılır ama OBV geride kalırsa pozisyon büyüklüğü azaltılabilir veya ek teyit beklenebilir.

## Tuzaklar ve Riskler

- Hacim verisi hatalı veya parçalıysa OBV yorumu da bozulur.
- Tek bir çok yüksek hacimli bar göstergeyi uzun süre etkileyebilir.
- OBV uyumsuzluğu bazen erken uyarıdır, zamanlama sinyali değildir.
- Likiditesi düşük sembollerde hacim sıçramaları yanıltıcı olabilir.

## PiyasaPilot'ta Kullan

Bu konu için hazır grafik köprüsü henüz yok. OBV'yi StrategySpec içinde fiyat kırılımını teyit eden ikinci koşul gibi kullanmak, tek başına OBV kesişimi kovalamaktan daha kontrollü bir yaklaşımdır.

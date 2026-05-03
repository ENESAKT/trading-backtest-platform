---
title: MFI — Para Akış Endeksi
slug: mfi
category: indikatorler
tags: [hacim, momentum, osilatör, para akışı]
difficulty: orta
indicator_key: MFI
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [hacim_verisi, likidite, esik_yanilmasi]
copy_policy: original_piyasapilot_content
---

MFI, fiyat hareketini hacimle birlikte değerlendiren bir momentum osilatörüdür. RSI'a benzer şekilde 0 ile 100 arasında okunur, fakat hareketin arkasındaki işlem yoğunluğunu da hesaba katmaya çalışır.

## Nedir?

MFI yüksek bölgelere çıktığında para akışının alım tarafında yoğunlaştığı, düşük bölgelere indiğinde satış baskısının arttığı düşünülebilir. Bu okuma hacim verisinin kalitesine doğrudan bağlıdır.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri:

```text
MFI(H,L,C,V,14)
```

Tepki fikri:

```text
CROSS_UP(MFI(H,L,C,V,14), 25) AND C > EMA(C,50)
```

Bu kural, düşük para akışı bölgesinden toparlanmayı ve fiyatın kısa trend filtresinin üzerinde kalmasını arar.

## Nasıl Okunur?

20 altı zayıf para akışı, 80 üstü ise yoğun alım bölgesi gibi izlenebilir. Ancak güçlü trendlerde MFI uzun süre yüksek veya düşük kalabilir; bu yüzden fiyat yapısı ve hacim rejimiyle birlikte okunmalıdır.

## Kullanım Örneği

Fiyat yatay destek üzerinde tutunurken MFI 20 altından yukarı dönüyorsa, satış baskısının azaldığı ve alıcıların geri döndüğü düşünülebilir. Fiyat yeni zirve yaparken MFI geride kalıyorsa hareketin katılımı zayıflamış olabilir.

## Tuzaklar ve Riskler

- Hacim verisi eksik veya parçalıysa sinyal güveni düşer.
- Düşük likiditeli sembollerde tek bar göstergede aşırı etki yaratabilir.
- 80 üstü otomatik satış, 20 altı otomatik alış anlamına gelmez.
- Uyumsuzluklar zamanlama değil, dikkat uyarısıdır.

## PiyasaPilot'ta Kullan

Bu makale için hazır grafik köprüsü yok. PiyasaPilot'ta MFI fikrini fiyat dönüşüne hacim teyidi ekleyen ikinci koşul olarak düşünmek, tek başına osilatör kovalamaktan daha kontrollüdür.

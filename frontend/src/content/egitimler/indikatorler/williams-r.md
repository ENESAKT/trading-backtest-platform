---
title: Williams %R
slug: williams-r
category: indikatorler
tags: [momentum, osilatör, aşırı alım, aşırı satım]
difficulty: orta
indicator_key: WILLR
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [trendde_erken_sinyal, esik_yanilmasi, whipsaw]
copy_policy: original_piyasapilot_content
---

Williams %R, kapanışın son fiyat aralığındaki konumunu ters ölçekle gösteren bir momentum osilatörüdür. Stochastic ailesine yakın bir mantık taşır; farkı, okumanın genellikle negatif bölgelerde yapılmasıdır.

## Nedir?

Gösterge 0 ile -100 arasında izlenir. 0'a yakın değerler fiyatın son aralığın üst kısmında, -100'e yakın değerler alt kısmında kapandığını anlatır. Bu, kısa vadeli momentumun nerede yoğunlaştığını görmeye yardım eder.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri:

```text
WILLR(H,L,C,14)
```

Dönüş fikri:

```text
CROSS_UP(WILLR(H,L,C,14), -80) AND C > EMA(C,50)
```

Bu kural, zayıf bölgeden yukarı dönüşü trend filtresiyle birlikte arar.

## Nasıl Okunur?

-20 üstü güçlü bölge, -80 altı zayıf bölge gibi izlenebilir. Ancak güçlü trendlerde bu bölgeler uzun süre korunabilir; bu yüzden sinyal, trend yönüyle birlikte değerlendirilmelidir.

## Kullanım Örneği

Fiyat yükselen trendde kısa süreli geri çekilirken Williams %R -80 altına iner ve tekrar yukarı dönerse tepki alımı fikri oluşabilir. Aynı hareket düşen trendde gelirse erken ve zayıf bir sinyal olabilir.

## Tuzaklar ve Riskler

- Uç bölge tek başına dönüş garantisi vermez.
- Yatay ve dar piyasada sık kesişim üretir.
- Kısa periyot hızlı ama gürültülü, uzun periyot daha gecikmelidir.
- Stochastic ile aynı anda kullanıldığında gereksiz tekrar yaratabilir.

## PiyasaPilot'ta Kullan

Hazır grafik köprüsü yok. Williams %R'yi PiyasaPilot'ta kısa vadeli momentum dönüş filtresi olarak, fiyat trendi ve hacim teyidiyle birlikte test etmek daha güvenlidir.

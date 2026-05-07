---
title: MOST — Moving Stop Loss
slug: most
category: indikatorler
tags: [trend, stop, hareketli ortalama, takip]
difficulty: ileri
indicator_key: MOST
related_strategies: []
source_courses: [fuat_akman_indikator, kivanc_hareketli_ortalamalar]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, whipsaw, parametre_overfit]
copy_policy: original_piyasapilot_content
---

MOST, hareketli ortalama etrafında iz süren stop mantığı kurmaya yarayan trend takip aracıdır. Amaç, trend devam ederken pozisyonu taşımak ve fiyat belirli bir eşiği bozduğunda riski azaltmaktır.

## Nedir?

MOST çizgisi fiyatın yönüne göre takip seviyesi üretir. Fiyat bu seviyenin üzerinde kaldığında yükseliş tarafı, altına geçtiğinde düşüş veya çıkış tarafı izlenir. Bu yüzden girişten çok pozisyon yönetimi için değerlidir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel gösterim:

```text
MOST(C,3,2)
```

Trend takip fikri:

```text
CROSS_UP(C, MOST(C,3,2)) AND C > EMA(C,50)
```

Çıkış tarafı:

```text
CROSS_DOWN(C, MOST(C,3,2))
```

## Nasıl Okunur?

Fiyat MOST çizgisinin üstünde kalıyorsa trend takip senaryosu korunabilir. Fiyat çizgiyi aşağı keserse stop, kar alma veya pozisyon azaltma gündeme gelir. Periyot ve yüzde ayarı, sinyalin hızını belirler.

## Kullanım Örneği

Orta vadeli bir yükselişte fiyat EMA 50 üstündeyken MOST yukarı yönlü kalıyorsa pozisyonu taşımak için iz süren bir çerçeve oluşur. Yatay piyasada aynı ayar gereksiz sık yön değiştirirse ATR veya ADX filtresi eklemek gerekir.

## Tuzaklar ve Riskler

- Parametreyi geçmişe göre fazla iyileştirmek canlıda kırılgan sonuç verir.
- Yatay piyasada sık kesişim küçük zarar serisi üretebilir.
- MOST gecikmeli çalışır; dip ve tepe yakalama aracı değildir.
- Stop mantığı gerçek işlemde boşluk ve slippage riskini ortadan kaldırmaz.

## PiyasaPilot'ta Kullan

Doğrudan preset köprüsü bu sürümde yok. StrategySpec içinde MOST'u giriş sinyalinden çok çıkış ve iz süren stop kuralı olarak modellemek daha planlı bir kullanım sağlar.

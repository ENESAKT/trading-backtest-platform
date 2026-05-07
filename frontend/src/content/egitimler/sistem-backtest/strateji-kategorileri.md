---
title: Strateji Kategorileri: Trend, Momentum, Mean Reversion
slug: strateji-kategorileri
category: sistem-backtest
tags: [trend, momentum, mean-reversion, strateji]
difficulty: orta
related_strategies: [sma_crossover, rsi_reversion, bollinger_reversion]
source_courses: [kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [piyasa_rejimi, kategori_karisimi, asiri_optimizasyon]
copy_policy: original_piyasapilot_content
---

Strateji kategorisi, sistemin hangi piyasa davranışından para kazanmayı hedeflediğini anlatır. Trend takip, momentum ve mean reversion aynı grafikte benzer indikatörleri kullanabilir; fark, sinyalin neyi varsaydığında saklıdır.

## Trend Takip

Trend takip sistemleri, hareketin başladıktan sonra devam edeceğini varsayar. Kesişimler, kanal kırılımları ve trend filtresi bu ailede sık görülür. Başarı, büyük hareketleri yakalarken yatay piyasadaki küçük zararları sınırlayabilmeye bağlıdır.

## Momentum

Momentum stratejileri, güçlü hareketin kısa vadede devam edebileceğini izler. Fiyat, hacim veya osilatör hızlanması kullanılır. Risk, hareketin geç fark edilmesi ve yorulmuş trendin sonuna yetişmektir.

## Mean Reversion

Mean reversion, fiyatın aşırı uzaklaştıktan sonra ortalamaya dönme eğilimini test eder. RSI, Bollinger Bandı ve fiyat-ortalama uzaklığı bu ailede kullanılır. Güçlü trend dönemlerinde erken ters sinyal üretme riski yüksektir.

## Kategori Seçerken

- Piyasa yatay mı, trendli mi?
- Strateji küçük sık kazanç mı, az ama büyük hareket mi bekliyor?
- Stop ve çıkış mantığı kategoriyle uyumlu mu?
- İşlem frekansı veri kalitesine uygun mu?
- Aynı portföyde benzer risk alan stratejiler birikiyor mu?

## Kullanım Örneği

`sma_crossover` trend takip fikrine, `rsi_reversion` ve `bollinger_reversion` ortalamaya dönüş fikrine yakındır. Aynı sembolde bu iki aileyi birlikte kullanmak, piyasa rejimi değiştiğinde davranış farkını görmeyi sağlar.

## Tuzaklar ve Riskler

- Her stratejiyi her piyasa rejiminde çalıştırmaya zorlamak hatalıdır.
- Bir stratejiye hem trend hem dönüş rolü yüklemek kuralları bulanıklaştırır.
- Kategori etiketi performans garantisi değildir.
- Aynı aileden çok sistem portföyde gerçek çeşitlendirme sağlamaz.

## PiyasaPilot'ta Kullan

Hazır preset'leri kategori gözlüğüyle karşılaştırabilirsin. Sonraki Backtest Lab fazlarında kategori metadata'sı kalite skoru ve portföy korelasyonuna bağlanacaktır.

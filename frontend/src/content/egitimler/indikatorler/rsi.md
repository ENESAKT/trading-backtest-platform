---
title: RSI — Göreceli Güç Endeksi
slug: rsi
category: indikatorler
tags: [momentum, osilatör, aşırı alım, aşırı satım]
difficulty: başlangıç
indicator_key: RSI
chart_indicator: rsi
related_strategies: [rsi_reversion]
source_courses: [fuat_akman_indikator, kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, uyumsuzluk_yanilmasi, trendde_erken_sinyal]
copy_policy: original_piyasapilot_content
---

RSI, fiyatın yükseliş ve düşüş hızını 0 ile 100 arasında okumaya yarayan bir momentum göstergesidir. En yaygın kullanım 14 periyot ve 30/70 bölgeleridir, ama bu eşikler piyasa karakterine göre tek başına karar sebebi olmamalıdır.

## Nedir?

RSI yüksek bölgelerde alıcıların yorulabileceğini, düşük bölgelerde satıcıların yorulabileceğini gösterir. Güçlü trendlerde RSI uzun süre uç bölgelerde kalabilir; bu nedenle trend filtresiyle birlikte kullanılır.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de temel seri şöyle çağrılır:

```text
RSI(C,14)
```

Basit bir dönüş fikri:

```text
CROSS_UP(RSI(C,14), 30) AND C > EMA(C,50)
```

Bu kural, RSI'ın aşırı satım bölgesinden yukarı dönmesini ve fiyatın kısa trend filtresinin üzerinde kalmasını arar.

## Nasıl Okunur?

30 altından dönüş tepki ihtimalini artırabilir. 70 üstü ise kar alma ya da momentumun aşırı ısınması için izlenebilir. 50 çizgisi çoğu senaryoda momentumun ağırlık merkezidir.

## Kullanım Örneği

Bir hisse EMA 50 üzerinde kalırken RSI 30 altından 35-40 bandına dönerse, fiyatın sadece düşüşü durdurmadığı, aynı zamanda momentumun da toparlandığı düşünülebilir. Tersi senaryoda RSI 70 üzerindeyken fiyat yeni zirve yapamıyorsa risk azaltma gündeme gelebilir.

## Tuzaklar ve Riskler

- RSI düşük diye fiyatın hemen döneceği varsayılmaz.
- Uyumsuzluklar bazen birkaç kez bozulur; stop planı olmadan kullanılmamalıdır.
- Kısa periyot daha hızlı ama daha gürültülü sinyal üretir.
- Eşikler her sembolde aynı davranmaz.

## PiyasaPilot'ta Kullan

Grafikte RSI alt panelini açıp 30/50/70 davranışını izleyebilirsin. Backtest tarafında `rsi_reversion`, aşırı bölgelerden dönüş fikrini hızlıca ölçmek için hazır başlangıçtır.

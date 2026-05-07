---
title: Parabolic SAR
slug: parabolic-sar
category: indikatorler
tags: [trend, stop, takip, dönüş, psar]
difficulty: başlangıç
indicator_key: PSAR
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: medium
needs_audio_transcript: true
risk_warnings: [whipsaw, yatay_piyasa, stop_mesafesi]
copy_policy: original_piyasapilot_content
---

Parabolic SAR, trend yönünü ve iz süren stop fikrini noktasal bir seriyle görünür kılar. Noktalar fiyatın altındaysa yükseliş takibi, üstündeyse düşüş takibi öne çıkar.

## Nedir?

SAR yaklaşımı, pozisyonun hangi tarafta takip edileceğini ve fiyat tersine döndüğünde stop seviyesinin nerede oluşabileceğini anlatır. Bu yüzden giriş sinyalinden çok pozisyon yönetimi ve çıkış disiplini için değerlidir.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de gösterim:

```text
PSAR(H,L,0.02,0.2)
```

Basit yön değişimi fikri:

```text
CROSS_UP(C, PSAR(H,L,0.02,0.2)) AND C > EMA(C,50)
```

Bu kural fiyatın SAR seviyesini yukarı geçmesini ve kısa trend filtresinin üzerinde kalmasını arar.

## Nasıl Okunur?

Noktalar fiyatın altında kalıyorsa iz süren destek gibi, üstünde kalıyorsa iz süren direnç gibi okunabilir. Noktaların taraf değiştirmesi trend dönüşü olasılığını artırır, ancak yatay piyasada bu değişimler sık sık bozulur.

## Kullanım Örneği

Trend yukarıyken fiyat Parabolic SAR noktalarının üzerinde kaldığı sürece pozisyon korunabilir. Fiyat noktaların altına kapanırsa çıkış veya risk azaltma kuralı tetiklenebilir. ATR ile stop mesafesi kontrolü eklemek aşırı dar çıkışları azaltabilir.

## Tuzaklar ve Riskler

- Yatay piyasada çok sık yön değiştirip küçük zararlar üretebilir.
- Hızlanma ayarı arttıkça daha hızlı ama daha gürültülü çalışır.
- Tek başına trend kalitesini ölçmez; ADX veya EMA filtresi gerekir.
- Haber boşluklarında stop seviyesi beklenen fiyattan çalışmayabilir.

## PiyasaPilot'ta Kullan

Doğrudan grafik köprüsü bu sürümde boş bırakıldı. Backtest fikri olarak Parabolic SAR'ı giriş sinyalinden çok iz süren çıkış veya risk azaltma kuralı şeklinde kullanmak daha tutarlı sonuç verir.

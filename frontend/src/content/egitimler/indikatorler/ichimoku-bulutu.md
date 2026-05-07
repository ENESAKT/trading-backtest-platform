---
title: Ichimoku Bulutu
slug: ichimoku-bulutu
category: indikatorler
tags: [trend, bulut, destek, direnç, momentum]
difficulty: ileri
indicator_key: ICHI
related_strategies: []
source_courses: [fuat_akman_indikator]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [gecikme, kalabalik_grafik, parametre_uyumsuzlugu]
copy_policy: original_piyasapilot_content
---

Ichimoku Bulutu, trend yönü, momentum ve olası destek-direnç bölgelerini tek sistemde okumaya çalışan kapsamlı bir göstergedir. En görünür parçası, ileriye taşınan iki çizginin oluşturduğu bulut bölgesidir.

## Nedir?

Bulutun üstündeki fiyat genellikle pozitif trend, altındaki fiyat negatif trend, bulut içindeki fiyat ise kararsız bölge gibi yorumlanır. Kısa ve orta çizgilerin ilişkisi momentum değişimini, gecikmeli çizgi ise fiyatla bağlam kontrolünü destekler.

## Nasıl Hesaplanır?

PiyasaPilot DSL'de ana bileşenler:

```text
ICHI_TENKAN(H,L,9)
ICHI_KIJUN(H,L,26)
ICHI_SENKOU_A(H,L,C,9,26)
ICHI_SENKOU_B(H,L,52)
ICHI_CHIKOU(C,26)
```

Trend filtresi örneği:

```text
C > ICHI_CLOUD_TOP(H,L,C,9,26,52) AND ICHI_TENKAN(H,L,9) > ICHI_KIJUN(H,L,26)
```

Bu kural fiyatın bulut üstünde kalmasını ve kısa çizginin orta çizgiden güçlü olmasını arar.

## Nasıl Okunur?

Fiyat bulut üstünde ve bulut genişliyorsa trend daha belirgin olabilir. Bulut içindeki hareketler kararsızlık alanıdır; sinyaller daha çok filtrelenmelidir. Bulutun yönü ve kalınlığı, fiyatın karşılaşabileceği alanı görselleştirir.

## Kullanım Örneği

Fiyat bulut üstüne çıktıktan sonra Kijun çizgisine geri çekilir ve yeniden yukarı dönerse trend devamı senaryosu kurulabilir. Aynı hareket bulut içinde olursa sinyal daha zayıftır; hacim ve genel piyasa yönüyle teyit beklemek daha sağlıklıdır.

## Tuzaklar ve Riskler

- Ichimoku çok bileşenli olduğu için grafiği kalabalıklaştırabilir.
- Her çizgiye ayrı sinyal anlamı yüklemek overfit riskini artırır.
- Bulut ileri taşındığı için görsel olarak güçlü görünür ama karar yine kapanmış barlarla verilmelidir.
- Varsayılan periyotlar her zaman dilimi ve piyasa için aynı derecede uygun olmayabilir.

## PiyasaPilot'ta Kullan

Bu sürümde Ichimoku için doğrudan grafik köprüsü yok. PiyasaPilot içinde en güvenli kullanım, bulutu trend rejimi filtresi; Tenkan-Kijun ilişkisini ise ikinci aşama momentum teyidi olarak düşünmektir.

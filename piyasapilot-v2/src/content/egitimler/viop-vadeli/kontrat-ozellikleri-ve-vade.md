---
title: Kontrat Özellikleri ve Vade
slug: kontrat-ozellikleri-ve-vade
category: viop-vadeli
tags: [kontrat, vade, sozlesme, uzlasma, viop]
difficulty: orta
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [vade_uyumsuzlugu, kontrat_carpani, likidite_riski, uzlasma_riski]
copy_policy: original_piyasapilot_content
---

Vadeli piyasada aynı dayanak varlık birden fazla kontratla işlem görebilir. Bu yüzden "hangi sembol?" sorusu tek başına yetmez; vade ayı, kontrat büyüklüğü, fiyat adımı ve uzlaşma türü de aynı dosyanın parçasıdır.

## Nedir?

Kontrat özellikleri, bir vadeli işlem sözleşmesinin standartlarını tanımlar. Vade ise kontratın hangi tarihe kadar işlem gördüğünü ve hangi dönemin beklentisini fiyatladığını gösterir.

## Nasıl Tanımlanır?

PiyasaPilot tarafında bir VIOP kontratı en az şu metadata ile temsil edilmelidir:

```text
CONTRACT(
  underlying: "BIST30",
  expiry: "YYYY-MM",
  multiplier: contract_size,
  tick: min_price_step,
  settlement: "cash_or_physical"
)
```

Bu şema işlem kuralı değil, test ve raporun hangi varsayımlarla üretildiğini saklayan güvenlik katmanıdır.

## Nasıl Okunur?

Yakın vade genellikle daha likit olur; uzak vadeler farklı beklentileri ve taşıma maliyetini yansıtabilir. Vade sonuna yaklaşıldığında fiyat davranışı, hacim dağılımı ve baz farkı değişebilir. Aynı dayanak için farklı vade kodlarını tek grafik gibi okumak hatalı sonuç üretir.

## Kullanım Örneği

Bir kullanıcı endeks vadeli kontratta trend stratejisi denemek ister. Test aralığı iki farklı vade dönemine yayılıyorsa sistem hangi gün hangi kontratı kullanacağını, pozisyonun ne zaman kapatılıp yeni vadeye taşınacağını ve eski-yeni fiyat farkının nasıl ele alınacağını bilmelidir.

## Tuzaklar ve Riskler

- Kontrat çarpanı unutulursa pozisyon büyüklüğü yanlış hesaplanır.
- Vade sonu davranışı normal günlerle aynı kabul edilirse rapor bozulabilir.
- Yakın vadedeki likidite uzak vadeye taşınmış gibi varsayılmamalıdır.
- Fiyat adımı ve minimum emir büyüklüğü yok sayılırsa gerçekleşebilirlik abartılır.

## PiyasaPilot'ta Kullan

VIOP backtest köprüsü bu aşamada kapalıdır. İçerik, ileride kontrat metadata zorunluluğu eklenirken kullanılacak kabul kontrolünü tarif eder: dayanak, vade, çarpan, fiyat adımı, uzlaşma ve likidite varsayımı olmadan sonuç yayınlanmamalıdır.

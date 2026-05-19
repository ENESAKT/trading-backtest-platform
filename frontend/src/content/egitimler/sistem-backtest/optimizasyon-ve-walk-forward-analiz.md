---
title: Optimizasyon ve Walk-Forward Analiz
slug: optimizasyon-ve-walk-forward-analiz
category: sistem-backtest
tags: [optimizasyon, walk-forward, out-of-sample, overfit]
difficulty: ileri
related_strategies: []
source_courses: [kivanc_algo_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [overfit, pencere_secimi, parametre_omru]
copy_policy: original_piyasapilot_content
---

Optimizasyon, strateji parametrelerinin hangi aralıkta daha dengeli çalıştığını arar. Walk-forward analiz ise bu aramayı geçmişin bir bölümünde yapıp sonucu sonraki görünmeyen bölümde sınayarak overfit riskini azaltmaya çalışır.

## Optimizasyon Nedir?

Optimizasyon, tek bir parametre değerine körü körüne inanmak yerine parametre alanını taramaktır. Amaç en yüksek getirili noktayı bulmak değil; komşu değerlerde de bozulmayan sağlam bölgeyi görmektir.

## Walk-Forward Nedir?

Walk-forward analizde veri pencerelere ayrılır. Her pencerede parametreler geçmiş bölümde seçilir, sonraki bölümde denenir. Böylece strateji yalnızca ezberlediği dönemde değil, takip eden piyasa koşulunda da sınanır.

## PiyasaPilot Bakışı

PiyasaPilot'ta WFA, klasik optimizasyon sonucunu gerçekçi bir eleme kapısından geçirir. Klasik rapor parlak ama WFA zayıfsa, sistemin canlıya hazır olmadığı varsayılır.

## Kontrol Listesi

- Optimize edilen parametre sayısı makul mü?
- Pencere uzunluğu strateji frekansına uygun mu?
- Out-of-sample bölüm optimizasyona karışmadan mı kullanıldı?
- Komşu parametreler de benzer kalite veriyor mu?
- WFA sonucu klasik optimizasyondan çok mu kopuyor?

## Kullanım Örneği

Bir MOST stratejisi geçmiş beş aylık bölümde optimize edilir, sonraki bir ayda seçilen parametreyle test edilir. Bu süreç yürüyen pencerelerle tekrarlandığında stratejinin değişen koşullara dayanıp dayanmadığı görülür.

## Tuzaklar ve Riskler

- Çok kısa pencere, parametrenin gerçek davranışını göstermez.
- Çok uzun pencere, değişen piyasa koşullarını saklayabilir.
- WFA'yı da tekrar tekrar ayarlamak yeni bir overfit katmanı yaratır.
- En iyi nokta yerine sağlam bölge aranmazsa sonuç kırılgan kalır.

## PiyasaPilot'ta Kullan

WFA modülü Backtest Lab'ın ağır işlerinden biridir. Tamamlandığında optimizasyon raporu, out-of-sample performans şeritleri ve WFE benzeri karşılaştırmalarla birlikte okunacaktır.

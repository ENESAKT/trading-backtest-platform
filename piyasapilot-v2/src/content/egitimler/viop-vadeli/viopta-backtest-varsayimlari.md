---
title: VIOP'ta Backtest Varsayımları
slug: viopta-backtest-varsayimlari
category: viop-vadeli
tags: [viop, backtest, varsayim, kontrat, teminat]
difficulty: ileri
related_strategies: []
source_courses: [yasar_vob, bolgun_vadeli_trade]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [overfit, lookahead, vade_gecisi, teminat_modeli, maliyet_eksigi]
copy_policy: original_piyasapilot_content
---

VIOP backtesti, spot hisse backtestinden daha fazla varsayım ister. Sinyal doğru olsa bile kontrat seçimi, vade geçişi, teminat, kaldıraç ve uzlaşma modeli açık değilse sonuç güvenilir kabul edilmemelidir.

## Nedir?

Backtest varsayımı, raporun hangi piyasa gerçeklerini basitleştirdiğini açıklar. VIOP'ta bu liste uzundur: hangi kontrat kullanıldı, pozisyon büyüklüğü nasıl hesaplandı, teminat ne kadar tutuldu, vade geçişi nasıl yapıldı, maliyet ve kayma nasıl modellendi?

## Nasıl Tanımlanır?

PiyasaPilot için güvenli minimum şema:

```text
VIOP_BACKTEST_ASSUMPTIONS(
  contract_source,
  rollover_rule,
  margin_model,
  leverage_limit,
  commission_slippage,
  settlement_handling
)
```

Bu alanlardan biri boşsa rapor "eğitim amaçlı simülasyon" olarak işaretlenmelidir.

## Nasıl Okunur?

VIOP raporunda toplam getiri kadar teminat kullanımı, en kötü ters hareket, maksimum açık pozisyon, vade geçiş günleri ve maliyet varsayımı da okunur. Sadece kapanış fiyatıyla üretilen rapor, gün içi teminat baskısını saklayabilir.

## Kullanım Örneği

Bir MACD stratejisi endeks vadelide iyi sonuç verir. Fakat test hep en likit yakın vadeyi geçmişe doğru kusursuz seçiyorsa, bu gerçek zamanlı karar akışını temsil etmeyebilir. Rollover kuralı ve işlem maliyeti raporun en üstünde görünmelidir.

## Tuzaklar ve Riskler

- Yakın vadeyi sonradan bilerek seçmek lookahead etkisi yaratabilir.
- Teminat çağrısı yok sayılırsa batabilecek strateji çalışır görünebilir.
- Vade sonu ve uzlaşma günleri normal işlem günü gibi modellenmemelidir.
- Çok optimize edilmiş parametreler kaldıraçla birleşince kayıp riski büyür.

## PiyasaPilot'ta Kullan

Bu aşamada VIOP backtest butonu bilinçli olarak boş bırakılır. Önce kontrat verisi, rollover, teminat ve maliyet varsayımları ürün seviyesinde kilitlenmelidir; aksi halde rapor kullanıcıyı yanıltabilir.

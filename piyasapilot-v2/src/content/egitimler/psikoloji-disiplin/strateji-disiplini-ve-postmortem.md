---
title: Strateji Disiplini ve Postmortem
slug: strateji-disiplini-ve-postmortem
category: psikoloji-disiplin
tags: [strateji, disiplin, postmortem, journal, süreç]
difficulty: orta
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [sonuc_odakliligi, kural_ihlali, veri_secimi, geriye_donuk_gerekce]
copy_policy: original_piyasapilot_content
---

Strateji disiplini, iyi görünen bir fikri her koşulda savunmak değil, baştan yazılmış kurala sadık kalıp işlem bittikten sonra soğukkanlı değerlendirme yapmaktır. Postmortem bu değerlendirmenin kayıt formatıdır.

## Nedir?

Postmortem, işlem kapandıktan sonra "neden kazandım veya kaybettim?" sorusunu süreç kalitesiyle cevaplar. Kural doğru çalıştı mı, giriş planlı mıydı, stop değişti mi, pozisyon büyüklüğü uygun muydu, kullanıcı işlem sırasında müdahale etti mi?

## Nasıl Ölçülür?

PiyasaPilot journal için basit kalite şeması:

```text
process_score =
  entry_rule_match +
  risk_defined_before_entry +
  no_mid_trade_rule_change +
  exit_reason_recorded
```

Kazanç ayrı, süreç puanı ayrı tutulur. Böylece kötü süreçle gelen şanslı kazançlar sistem başarısı sanılmaz.

## Nasıl Okunur?

Bir işlem para kazandırdıysa bile kurala uymadıysa risklidir. Bir işlem zarar ettiyse ama plana tamamen uyduysa değerli veri üretmiş olabilir. Disiplinin amacı kaybı yok etmek değil, karar kalitesini tekrar ölçülebilir hale getirmektir.

## Kullanım Örneği

Kullanıcı bir kırılım stratejisiyle işlem açar. Fiyat hedefe gitmeden önce panikle çıkar ve sonra hedefe ulaşır. Postmortem sonucu "strateji başarısız" değil, "çıkış kuralı ihlal edildi" olarak kaydeder. Bu ayrım sonraki testleri korur.

## Tuzaklar ve Riskler

- Sadece karlı işlemleri incelemek seçilim yanlılığı üretir.
- Postmortem işlem sırasında değil, kapanıştan sonra yapılmalıdır.
- Kural dışı kazançlar stratejiye eklenirse overfit riski artar.
- Çok fazla serbest metin, raporun karşılaştırılmasını zorlaştırır.

## PiyasaPilot'ta Kullan

Bu içerik paper journal ve strateji raporlarına hazırlık niteliğindedir. Her paper işlem için giriş nedeni, risk planı, çıkış nedeni ve kullanıcı müdahalesi ayrı alanlarda saklanmalıdır.

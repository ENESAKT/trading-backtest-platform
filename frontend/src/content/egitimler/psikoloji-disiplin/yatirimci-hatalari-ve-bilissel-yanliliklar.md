---
title: Yatırımcı Hataları ve Bilişsel Yanlılıklar
slug: yatirimci-hatalari-ve-bilissel-yanliliklar
category: psikoloji-disiplin
tags: [psikoloji, bilissel-yanlilik, davranissal-finans, risk]
difficulty: başlangıç
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [asiri_ozguven, tanidiklik_yanliligi, suru_davranisi, gurultu_sinyali]
copy_policy: original_piyasapilot_content
---

Yatırımcı hatalarının çoğu bilgi eksikliğinden değil, bilginin stres altında yanlış işlenmesinden doğar. PiyasaPilot'ta psikoloji başlıkları bu yüzden "daha cesur işlem" için değil, işlemi yavaşlatan ve kayıt altına alan kontrol katmanı için kullanılır.

## Nedir?

Bilişsel yanlılık, karar verirken bazı bilgileri gereğinden fazla, bazılarını ise gereğinden az önemsemektir. Tanıdık şirkete aşırı güvenmek, yükselen fiyatın peşinden koşmak, zarardaki pozisyonu haklı çıkarmak veya her haberi sinyal sanmak bu grubun tipik örnekleridir.

## Nasıl Ölçülür?

PiyasaPilot journal kaydında her işlem için davranış etiketi tutulabilir:

```text
BEHAVIOR_TAGS = [fomo, familiarity_bias, revenge_trade, confirmation_bias]
trade_quality = rule_match AND NOT high_emotion_tag
```

Amaç kullanıcının kişiliğini etiketlemek değil, işlem kalitesini bozan tekrar eden davranışları görünür kılmaktır.

## Nasıl Okunur?

Tek bir hatalı işlem psikoloji sorunu sayılmaz. Aynı etiketin belirli piyasa koşullarında tekrar etmesi önemlidir: hızlı yükselişlerde kovalamak, düşüşlerde planı iptal etmek, zarar büyürken gerekçe üretmek veya işlem sayısını stresle artırmak gibi.

## Kullanım Örneği

Kullanıcı üç hafta içinde beş kez yalnızca gün içi haber akışıyla işlem açar ve bu işlemler strateji kuralıyla eşleşmez. Journal bu işlemleri "gürültü" etiketiyle bir araya getirirse sorun fiyat tahmininden çok süreç ihlali olarak görünür.

## Tuzaklar ve Riskler

- Yanlılık farkındalığı tek başına risk yönetimi değildir.
- Her kaybı psikolojiye bağlamak strateji hatasını saklayabilir.
- Her kazancı beceri saymak aşırı özgüveni büyütür.
- Eğitim metni kişisel finansal tavsiye yerine süreç disiplini olarak okunmalıdır.

## PiyasaPilot'ta Kullan

Bu makalede aktif strateji köprüsü yoktur. En doğru kullanım, paper journal ve postmortem ekranlarında işlem gerekçesi, duygu etiketi ve kural uyumu alanlarını birlikte tutmaktır.

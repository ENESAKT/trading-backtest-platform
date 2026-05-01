---
title: Stop-Loss Koyamamak: Kayıptan Kaçınma
slug: stop-loss-koyamamak-kayiptan-kacinma
category: psikoloji-disiplin
tags: [stop-loss, kayip, prospect, disiplin, risk]
difficulty: orta
related_strategies: []
source_courses: [yatirimci_psikolojisi]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [stop_ihmali, kaybi_buyutme, pozisyon_asiri_buyume, plan_disina_cikma]
copy_policy: original_piyasapilot_content
---

Stop-loss koyamamak, çoğu zaman fiyat bilgisinden çok kaybı zihinsel olarak kabul edememe sorunudur. Kayıp büyüdükçe işlem artık bir strateji kararı olmaktan çıkıp "eski fikri savunma" davranışına dönüşebilir.

## Nedir?

Kayıptan kaçınma, aynı büyüklükteki kaybın aynı büyüklükteki kazançtan daha sert hissedilmesi eğilimidir. Bu eğilim yatırımcıyı stop seviyesini ertelemeye, zarardaki pozisyonu gerekçelendirmeye veya ortalama düşürerek riski büyütmeye itebilir.

## Nasıl Ölçülür?

PiyasaPilot'ta stop disiplini işlem açılmadan önce kilitlenmelidir:

```text
planned_risk = entry_price - stop_price
rule_breach = close < stop_price AND position_still_open
```

Stop seviyesi sonradan değiştiriliyorsa journal bunun nedenini ayrıca kaydetmelidir.

## Nasıl Okunur?

Sağlıklı stop, rastgele bir fiyat çizgisi değil, stratejinin yanıldığını kabul ettiği seviyedir. Stop çok dar ise normal gürültüyle çalışır; çok geniş ise kaybı kontrol etmez. Psikoloji tarafındaki kritik soru şudur: seviye baştan mı belirlendi, yoksa zarar büyüdükten sonra mı icat edildi?

## Kullanım Örneği

Bir kullanıcı destek kırılırsa çıkacağını yazar, fakat kırılım geldiğinde "biraz daha izleyeyim" diyerek pozisyonu açık tutar. Sonraki postmortem'de kayıp büyüklüğünden önce süreç ihlali kaydedilir: stop kuralı vardı, uygulanmadı.

## Tuzaklar ve Riskler

- Stop koymak kaybı sıfırlamaz; yalnızca hasarı sınırlar.
- Her stop sonrası fiyat döndü diye stop disiplini iptal edilmemelidir.
- Stop seviyesini zarardayken genişletmek risk profilini değiştirir.
- Kaldıraçlı işlemlerde stop ihlali teminat riskine hızla dönüşebilir.

## PiyasaPilot'ta Kullan

Bu başlık paper trading ve postmortem akışına bağlanır. İşlem açmadan önce giriş, stop, hedef ve iptal koşulu yazılmalı; işlem kapanınca plana uyulup uyulmadığı ayrı metrik olarak izlenmelidir.

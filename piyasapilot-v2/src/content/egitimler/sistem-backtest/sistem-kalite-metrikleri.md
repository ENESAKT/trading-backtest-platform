---
title: Sistem Kalite Metrikleri: Sharpe, PF, Max DD
slug: sistem-kalite-metrikleri
category: sistem-backtest
tags: [sharpe, profit-factor, max-drawdown, metrik]
difficulty: orta
related_strategies: []
source_courses: [kivanc_algo_trade, fuat_sistem_trading]
source_method: frame_ocr
source_confidence: medium
needs_audio_transcript: true
risk_warnings: [tek_metrik_yanilgisi, az_islem, metrik_makyaji]
copy_policy: original_piyasapilot_content
---

Sistem kalite metrikleri, backtest sonucunu tek bir getiri sayısından çıkarıp risk, istikrar ve işlem kalitesiyle birlikte okumayı sağlar. Sharpe, Profit Factor ve Max Drawdown farklı sorular sorar; hiçbiri tek başına yeterli değildir.

## Sharpe

Sharpe, getirinin oynaklığa göre ne kadar verimli üretildiğini ölçmeye çalışır. Daha düzgün sermaye eğrileri genelde daha iyi görünür. Ancak çok oynak veya seyrek işlem yapan stratejilerde yanıltıcı olabilir.

## Profit Factor

Profit Factor, brüt kazançların brüt zararlara oranıdır. 1'in altı zarar eden yapıya, 1'in üstü kâr üretme potansiyeline işaret eder. Fakat az işlemli stratejide tek büyük kazanç oranı şişirebilir.

## Max Drawdown

Max Drawdown, sermaye eğrisindeki en büyük tepe-dip kaybını gösterir. Kullanıcı açısından en psikolojik metriktir; çünkü sistem kârlı olsa bile dayanılması zor düşüşler paper aşamasında terk edilmesine yol açabilir.

## Kontrol Listesi

- Toplam getiri Max DD'ye göre anlamlı mı?
- Profit Factor işlem sayısıyla destekleniyor mu?
- Sharpe tek bir sakin dönemin ürünü mü?
- Kazanç/zarar dağılımı birkaç outlier'a mı bağlı?
- Metrikler maliyet sonrası mı hesaplandı?

## Kullanım Örneği

Yüzde 60 getiri ve yüzde 55 Max DD üreten strateji, yüzde 25 getiri ve yüzde 8 Max DD üreten stratejiden daha iyi olmayabilir. Kalite, kullanıcının sermayeyi koruyarak sistemi sürdürebilmesiyle ilgilidir.

## Tuzaklar ve Riskler

- Tek metriğe göre sistem seçmek hatalıdır.
- Kısa test aralığında Sharpe yapay olarak iyi görünebilir.
- Profit Factor komisyon kapalıyken şişebilir.
- Max DD geçmişte görülmeyen daha kötü senaryoyu garanti dışı bırakmaz.

## PiyasaPilot'ta Kullan

Backtest kalite skoru, bu metrikleri veri kapsama, işlem sayısı, maliyet ve out-of-sample sonucu ile birlikte okuyacak. Böylece "en yüksek getiri" ile "en dengeli sistem" ayrı gösterilecektir.

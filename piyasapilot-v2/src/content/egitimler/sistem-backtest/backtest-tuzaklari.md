---
title: Backtest Tuzakları: Overfit, Lookahead, Data Bias
slug: backtest-tuzaklari
category: sistem-backtest
tags: [overfit, lookahead, veri-on-yargisi, backtest]
difficulty: orta
related_strategies: []
source_courses: [kivanc_algo_trade, fuat_sistem_trading]
source_method: frame_ocr
source_confidence: high
needs_audio_transcript: true
risk_warnings: [overfit, lookahead, data_bias, survivorship_bias]
copy_policy: original_piyasapilot_content
---

Backtest tuzakları, stratejinin gerçekten iyi olduğu için değil, testin yanlış kurulduğu için iyi görünmesine yol açar. PiyasaPilot'ta iyi rapor, yalnızca yüksek getiri değil; sızıntısız veri, makul örneklem ve gerçekçi varsayımlar demektir.

## Overfit

Overfit, parametrelerin geçmiş veriye fazla uydurulmasıdır. Çok sayıda koşul ve parametre denendiğinde rapor parlayabilir, fakat canlı piyasada aynı davranış tekrarlanmayabilir.

## Lookahead

Lookahead, stratejinin işlem anında bilinemeyecek veriyi kullanmasıdır. Bar kapanmadan kapanış bilgisini kullanmak, gelecekte oluşacak high/low değerleriyle emir doldurmak veya sinyali geçmişe yazmak bu aileye girer.

## Data Bias

Data bias, test evreninin gerçeği temsil etmemesidir. Sadece kazandıran sembolleri seçmek, delist olmuş hisseleri dışarıda bırakmak veya kısa bir boğa dönemini tüm piyasa sanmak raporu yanıltır.

## Kontrol Listesi

- Parametre sayısı strateji fikrine göre makul mü?
- Sinyal sadece bar kapanışında bilinen bilgiyle mi oluşuyor?
- Test evreni kaybeden örnekleri de içeriyor mu?
- Out-of-sample veya WFA doğrulaması var mı?
- İşlem sayısı istatistiksel yorum için yeterli mi?

## Kullanım Örneği

Bir RSI stratejisi için 2'den 50'ye kadar her parametre denenip yalnızca en yüksek getirili sonuç seçilirse overfit riski büyür. Aynı parametre komşu değerlerde de dengeli çalışmıyorsa sistem kırılgandır.

## Tuzaklar ve Riskler

- En iyi tek sonucu raporlamak karar kalitesini düşürür.
- Sinyali geçmiş mumlara yeniden çizmek repaint etkisi yaratır.
- Veri eksikleri genellikle güzel görünen sonuçların arkasında saklanır.
- Çok az işlemle yüksek getiri güvenilir değildir.

## PiyasaPilot'ta Kullan

Bu makale, backtest raporundaki kalite kapılarının gerekçesidir. WFA, Monte Carlo, veri kapsama ve minimum işlem sayısı kontrolleri tamamlanmadan paper aşamasına geçilmemelidir.

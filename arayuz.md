# Quant Engine — Arayüz Planı (UI/UX) — v2 Revize

## Tasarım Felsefesi

Hedef **şık efektler değil**, **güven, hız, karşılaştırma ve denetlenebilirlik**. Bir araştırma terminali gibi bilgi yoğunluğu yüksek, okunabilir, profesyonel bir arayüz.

- **Dark mode** ama sade: Koyu gri arka plan, beyaz metin, yeşil (kâr) / kırmızı (zarar)
- **Glassmorphism veya animasyon YOK** — her piksel bilgi taşımalı
- **İlk versiyon:** Streamlit veya Dash (Python, hızlı prototip)
- **Kalıcı versiyon:** FastAPI + React/Next.js (ihtiyaç olursa, sonra)

---

## Tam Otomatik Veri Çekme

- Cronjob/launchd ile her gün saat **19:00'da** otomatik uyanır
- Sadece eksik günleri çeker (delta fetch)
- İnternet koparsa gece **00:00'a kadar** her saat tekrar dener
- Başarı/hata durumunda bildirim (Telegram botu veya arayüz paneli)
- Manuel "Şimdi Güncelle" butonu da mevcut

---

## Ekranlar

### 1. Dashboard (Ana Panel)
Sisteme ilk girişte görülen özet.
- **Veri güncelliği:** Son başarılı fetch ne zaman? Hangi semboller güncel, hangileri değil?
- **Veri kalite uyarıları:** Boşluk, outlier, eksik gün sayısı
- **Son backtest koşuları:** Tarih, strateji, sonuç (Sharpe, MaxDD) — tıklanabilir
- **Sistem durumu:** Toplam veri satır sayısı, disk kullanımı, motor versiyon

### 2. Data Station (Veri İstasyonu)
Veritabanının röntgeni.
- **Sembol bazlı coverage:** Her hisse için ilk tarih / son tarih / satır sayısı
- **Boşluk haritası:** Hangi günlerde veri eksik?
- **Outlier listesi:** %20+ günlük değişim gösteren günler (olası split/temettü)
- **Kaynak ve adjustment durumu:** raw / clean / adjusted / features hangi aşamada?
- **"Yeni Hisse Ekle" ve "Verileri Güncelle"** butonları

### 3. Strategy Builder (Strateji Kurucu)
Hiç kod yazmadan senaryo kurma alanı.
- **Strateji seçimi:** Açılır menüden (SMA Crossover, RSI, Bollinger vb.)
- **Parametre paneli:** Slider'lar ile ayar (fast: 10, slow: 50)
- **Universe seçimi:** "BIST30", "Bankalar", "Sadece THYAO" — çoklu seçim
- **Tarih aralığı:** Başlangıç / bitiş
- **Maliyet modeli:** Komisyon oranı, slippage seçimi
- **Risk limitleri:** Max pozisyon %, max drawdown %
- **Warm-up bars:** İlk kaç bar sinyal üretmesin?
- **🚀 "TEST ET" butonu**

### 4. Backtest Lab (Sonuç Laboratuvarı)
Test bittikten sonra açılan analiz ekranı.
- **Equity curve** (sermaye eğrisi) — interaktif, fareyle detay
- **Drawdown grafiği** — maximum drawdown vurgulanmış
- **Benchmark kıyası** — Buy & Hold ile yan yana
- **Performans kartları:** Net Kâr, Sharpe, MaxDD, Win Rate, Profit Factor
- **Gross vs Net ayrımı** — komisyon etkisi ne kadar?
- **Aylık getiri ısı haritası** (heatmap)
- **Trade tablosu:** Giriş/çıkış/kâr/zarar, filtrelenebilir
- **Assumptions panel:** Bu sonuç hangi varsayımlarla üretildi? (slippage, fill model, warm-up)

### 5. Run Compare (Koşu Karşılaştırma)
Birden fazla backtest koşusunu yan yana analiz etme.
- **Tablo:** Koşu ID, tarih, strateji, parametreler, Sharpe, MaxDD, net kâr
- **Equity curve overlay:** Seçilen koşuların sermaye eğrilerini üst üste çiz
- **Parametre diff:** İki koşu arasında ne değişti?
- **Config snapshot:** Her koşunun ayarlarına tıkla ve gör

### 6. Optimization (Parametre Optimizasyonu)
Strateji parametrelerinin en sağlam kombinasyonunu bulma.
- **Parametre heatmap:** X: fast_period, Y: slow_period, renk: Sharpe (veya net kâr)
- **Walk-forward fold sonuçları:** Her fold'un in-sample/out-of-sample performansı
- **Stability grafiği:** Parametreyi biraz değiştirince sonuç ne kadar bozuluyor?
- **Cost sensitivity:** 2bps / 5bps / 10bps'de performans nasıl değişiyor?

### 7. Trade Inspector (İşlem Denetçisi)
"Bu işlem neden açıldı?" sorusuna cevap veren debug aracı.
- **Audit trail:** Sinyal → Emir → Dolum → Pozisyon → PnL zinciri
- **O anın grafiği:** İşlem açıldığı andaki fiyat + indikatör durumu
- **Dolum detayı:** Hangi fiyattan, ne kadar slippage ile doldu?
- **Filtreleme:** En kârlı / en zararlı / en büyük / belirli tarih

---

## Uygulama Sırası

1. **Önce motor** — UI olmadan, terminalde çalışır, HTML rapor üretir
2. **Streamlit MVP** — Motor hazır olduktan sonra, 1-2 günde basit ama işlevsel arayüz
3. **React/Next.js** — Sadece Streamlit yetersiz kalırsa, çok sonra

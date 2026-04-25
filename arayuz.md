# 🖥️ Quant Engine — Arayüz ve Otomasyon Planı (UI/UX)

Bu doküman, arka planda çalışan güçlü backtest motorunun (Quant Engine) ileride nasıl bir web arayüzü ile kontrol edileceğini ve veri süreçlerinin nasıl tam otomatik hale getirileceğini detaylandırır.

## 1. 🤖 Tam Otomatik Veri Çekme (Data Otomasyonu)

Senin hiçbir butona basmana gerek kalmadan verilerin güncellenmesi sistemin temel taşıdır.

*   **Nasıl Çalışacak?** İşletim sisteminin arka plan görev yöneticisi (Mac için `launchd` veya `cronjob`) kullanılacak.
*   **Zamanlama:** Sistem her gün Borsa İstanbul seans kapanışından sonra (örneğin saat **19:00'da**) uyanacak.
*   **Akıllı Çekim (Delta Fetch):** Sadece "eksik olan günleri" çekecek. Örneğin dün veri çekildiyse, bugün sadece bugünün 1 günlük verisini indirecek. Bu işlem saniyeler sürecek.
*   **Hata Yönetimi:** İnternet koparsa veya Yahoo Finance yanıt vermezse, sistem gece **00:00'a kadar her saat başı** tekrar deneyecek.
*   **Bildirim:** İşlem başarıyla bittiğinde veya kalıcı bir hata olduğunda sana (örneğin Telegram botu üzerinden veya arayüzdeki bildirim panelinden) sessiz bir bildirim gönderecek.

---

## 2. 🎨 Arayüz Felsefesi ve Tasarım Dili

Hedefimiz sıradan bir excel tablosu görünümü değil, **premium, fütüristik ve karanlık (Dark Mode) ağırlıklı bir Bloomberg Terminal alternatifi** yaratmak.

*   **Renk Paleti:** Gece mavisi/siyah arka planlar (`#0B0E14`), vurgular için neon yeşil (kâr) ve siber kırmızı (zarar).
*   **Cam Efekti (Glassmorphism):** Menüler ve kartlar yarı şeffaf, arka planı hafif bulanık gösteren modern bir yapıda olacak.
*   **Canlılık:** Tıkladığında, fareyi grafikte gezdirdiğinde ufak mikro-animasyonlar ile sistemin "yaşadığını" hissedeceksin.
*   **Teknoloji:** Arka uç (Backend) **FastAPI** (Python), Ön yüz (Frontend) ise **React/Next.js** (veya Python tabanlı çok şık bir **Streamlit/Dash** tasarımı) ile yapılacak.

---

## 3. 📱 Ekranlar ve Menüler

Sisteme girdiğinde sol tarafta şık bir menü çubuğu olacak. İşte sayfalar:

### 🏠 1. Ana Gösterge Paneli (Dashboard)
Sisteme ilk girdiğinde seni karşılayan özet ekran.
*   **Sistem Durumu:** Veritabanında kaç milyon satır veri var? Son veri güncellemesi ne zaman yapıldı? (Yeşil tik ile gösterilecek).
*   **Aktif Stratejiler:** Canlıda veya sanal takipte (paper trading) olan stratejilerinin bugünkü kâr/zarar durumu.
*   **Piyasa Özeti:** BIST30'un o günkü genel durumu (küçük bir ısı haritası - Heatmap).

### 📥 2. Veri İstasyonu (Data Pipeline)
Veri tabanının kalbi.
*   **Hisse Listesi:** Sistemde kayıtlı tüm hisselerin listesi. Yanlarında ne kadarlık geçmiş verileri olduğu yazar (Örn: `THYAO - 2015'ten bugüne (1.2M Satır)`).
*   **Manuel Tetikleme:** Otomasyon dışında, istersen "Tüm Verileri Şimdi Güncelle" veya "Yeni Hisse Ekle" butonları.
*   **Kalite Skoru:** Verilerde boşluk veya anormallik varsa sistem burada uyarı verir (Örn: *"GARAN verisinde 3 gün boşluk tespit edildi"*).

### 🧪 3. Senaryo ve Strateji Kurucu (Strategy Builder)
İşte burası senin oyun alanın. Hiç kod yazmadan veya çok az kodla yeni fikirler deneyeceğin yer.
*   **Strateji Seçimi:** Önceden yazdığımız algoritmaları (Örn: "Hareketli Ortalama Kesişimi", "RSI Aşırı Satım", "Bollinger Kırılımı") bir açılır menüden seçersin.
*   **Parametre Paneli:** Seçtiğin stratejinin ayarları sliders (kaydırma çubukları) ile önüne gelir. 
    *   *Örnek:* "Kısa Ortalama: [ 10 ]", "Uzun Ortalama: [ 50 ]". Bunları fareyle sağa sola çekerek ayarlarsın.
*   **Hisse Seçimi:** Bu stratejiyi nerede test etmek istiyorsun? "Sadece Bankalar", "Tüm BIST30", "Sadece THYAO". Tıkla ve seç.
*   **Tarih Aralığı:** Hangi yıllar arasında test edilecek? (Örn: 2018-2024).
*   **🚀 "TEST ET" Butonu:** En altta devasa, dikkat çekici bir buton. Buna bastığında motor arkada saniyeler içinde milyonlarca hesaplama yapar.

### 📈 4. Backtest Laboratuvarı (Raporlar ve Sonuçlar)
"Test Et" butonuna bastıktan sonra açılan sihirli ekran. Her şey görselleştirilmiştir.
*   **Sermaye Eğrisi (Ana Grafik):** Ekranın ortasında kocaman bir grafik. Paranın zaman içindeki büyümesini gösterir. Fareyle grafikte gezindiğinde o günkü bakiyeni anlık görürsün.
*   **Performans Kartları (En Üstte):** 
    *   `Net Kâr: +%340` (Yeşil)
    *   `Maksimum Düşüş (Drawdown): -%12` (Kırmızı)
    *   `Kazanma Oranı (Win Rate): %65`
    *   `Toplam İşlem: 142`
*   **Aylık Isı Haritası (Heatmap):** Hangi ay yüzde kaç kâr/zarar ettiğini gösteren satranç tahtası gibi bir tablo. Kârlı aylar koyu yeşil, zararlı aylar koyu kırmızı. Bu sayede stratejinin hangi dönemlerde çuvalladığını şıp diye anlarsın.
*   **İşlem Dökümü (Tablo):** En altta, yapılan tüm al-sat işlemlerinin excel benzeri ama çok şık bir tablosu. İstersen bu sonuçları "Excel'e Aktar" butonu ile bilgisayarına indirebilirsin.

### ⚙️ 5. Ayarlar (Settings)
*   Başlangıç paranı (Örn: 100.000 TL), aracı kurumunun senden kestiği komisyon oranını değiştirebileceğin bölüm.

---

## 🎯 Sonuç: Ne Elde Edeceksin?
Motor (Backend) sana hızı ve doğruluğu sağlayacak. Bu planladığımız Arayüz (Frontend) ise senin bu gücü bir orkestra şefi gibi parmaklarının ucuyla, görsel bir şölen içinde yönetmeni sağlayacak. Strateji üretmek sıkıcı bir kod yazma işinden çıkıp, zevkli bir strateji oyununa dönüşecek.

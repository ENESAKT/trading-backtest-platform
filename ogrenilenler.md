# Öğrenilenler

## Frontend / UI
- PiyasaPilot v2.0 frontend UI/UX incelemesi browser agent üzerinden yapıldı. Sembol arama bileşeninde sürekli 'Sonuç yok' dönmesi, Mali Analiz sayfasında seçilen hisseye rağmen başlığın BTCUSDT kalması ve Grafik bileşenlerinde zaman dilimi (timeframe) değiştiğinde yaşanan siyah ekran/takılma gibi kritik senkronizasyon ve state management hataları tespit edilerek YAPILACAKLAR.md dosyasına detaylıca eklendi.
- Derinlemesine QA testleri sonucunda; Mali Analiz sekmesinde veriler başarıyla yüklense dahi "⚠ Veri çekilemedi" hata uyarısının asılı kalması, Bilanço tablosundaki bazı kalemlerin (Örn: Diğer Alacaklar) mükerrer (duplicate) render edilmesi ve Strateji sayfasındaki "Çalıştır" butonunun zor tıklanabilir DOM konumlandırma sorunları gibi spesifik uç durum (edge-case) hataları tespit edilerek rapora işlendi.

## Mimari / Agent Sistemi
- "Browser QA Tester" (Tarayıcı Kalite Güvence Test Uzmanı) adında yeni bir agent workflow (iş akışı) yeteneği oluşturuldu ve `.agents/skills/browser-qa-tester/SKILL.md` dizinine eklendi. Bu yetenek, sistemin gelecekte de derinlemesine ve otonom frontend QA testleri yapabilmesini standartlaştırmaktadır.

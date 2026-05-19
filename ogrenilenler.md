# Öğrenilenler

## Frontend / UI
- 2026-05-19 canlı Chrome QA'da production terminalin eski `piyasapilotu.com` üzerinde açıldığı, yeni `piyasapilot.com` domaininin Chrome'da `ERR_BLOCKED_BY_CLIENT` verdiği, `/login` gibi SPA public route'larının frontend nginx fallback eksikliği nedeniyle `404 Not Found` döndüğü ve grafik/haber API çağrılarının `APIKeyMiddleware` yüzünden `401/429` hatasına düştüğü görüldü. Ayrıntılı bulgular ve yapılacaklar `docs/planning/planlama.md` içindeki "Canlı Hata Denetimi — 2026-05-19" bölümüne işlendi.
- PiyasaPilot v2.0 frontend UI/UX incelemesi browser agent üzerinden yapıldı. Sembol arama bileşeninde sürekli 'Sonuç yok' dönmesi, Mali Analiz sayfasında seçilen hisseye rağmen başlığın BTCUSDT kalması ve Grafik bileşenlerinde zaman dilimi (timeframe) değiştiğinde yaşanan siyah ekran/takılma gibi kritik senkronizasyon ve state management hataları tespit edilerek YAPILACAKLAR.md dosyasına detaylıca eklendi.
- Derinlemesine QA testleri sonucunda; Mali Analiz sekmesinde veriler başarıyla yüklense dahi "⚠ Veri çekilemedi" hata uyarısının asılı kalması, Bilanço tablosundaki bazı kalemlerin (Örn: Diğer Alacaklar) mükerrer (duplicate) render edilmesi ve Strateji sayfasındaki "Çalıştır" butonunun zor tıklanabilir DOM konumlandırma sorunları gibi spesifik uç durum (edge-case) hataları tespit edilerek rapora işlendi.

## Mimari / Agent Sistemi
- "Browser QA Tester" (Tarayıcı Kalite Güvence Test Uzmanı) adında yeni bir agent workflow (iş akışı) yeteneği oluşturuldu ve `.agents/skills/browser-qa-tester/SKILL.md` dizinine eklendi. Bu yetenek, sistemin gelecekte de derinlemesine ve otonom frontend QA testleri yapabilmesini standartlaştırmaktadır.

## Altyapı / DevOps
- CI/CD ve DevOps kurguları kapsamında, AWS EC2 deploy ve yedekleme scriptleri (idempotent bash) başarıyla hazırlandı. Sentry ve SQLite yedekleme-restore drill testleri için betikler eklendi; `nginx.prod.conf` içerisinde `/status` endpoint'i doğrudan fastapi `health` dönüşüne proxy'lenerek monitoring yetenekleri iyileştirildi.

## Backend / Güvenlik
- Tüm korumalı API endpoint'lerine `Depends(get_current_user)` JWT auth guard'ı eklendi (backtest, paper, strategy-lab, news, mali-analiz, alerts). `/api/health` ve auth endpoint'leri herkese açık kaldı. Test: 54 parametrize senaryosu ile `test_auth_guards.py` oluşturuldu.
- `PlanLimits` dataclass'ına `max_saved_strategies` ve `paper_trading` bool alanları eklendi. Free plan: max 3 strateji, paper trading kapalı (0 paper account). Paper trading POST endpoint'leri `dependencies=[Depends(require_paper_trading)]` ile korundu.
- Billing router (`/api/billing/*`) oluşturuldu. `STRIPE_SECRET_KEY` yokken tüm endpoint'ler 503 döndürür — graceful degradation. SQLite `stripe_events` tablosu ile webhook idempotency sağlanıyor.
- Email template'leri Jinja2 + inline CSS ile yeniden tasarlandı. Marka renkleri: `#0f1117` (arka plan), `#ffb020` (accent), `#e2e8f0` (metin). `payment_success.html` yeni oluşturuldu.
- `SQLitePool` thread-safe connection pool modülü (`backend/db/pool.py`) oluşturuldu. WAL modu, busy_timeout, cache_size pragmaları varsayılan. `/api/health` endpoint'i artık `db_pools` istatistiklerini döndürüyor.

## Test / E2E
- Playwright E2E testlerinde `selectOption` komutunun düzgün çalışması için öncesinde mutlaka `focus()` çağrılmalıdır, aksi takdirde testler timeout'a düşmektedir.
- Lightweight-charts kütüphanesi DOM'a birden fazla canvas elementi eklediğinden, chart görünürlük testlerinde `locator('canvas')` yerine `locator('canvas').first()` kullanılarak Strict Mode ihlalleri önlenmiştir.
- `/api/auth/me` endpoint'i mocklanırken FastAPI backend'inin standart payload yapısına uygun olarak kullanıcı objesi `user` anahtarı yerine `data` anahtarı içerisinde döndürülmelidir. Aksi takdirde frontend auth layer, kullanıcıyı `guest` olarak işaretleyip premium özellikleri (Plan Gate) kilitler.
- Yeni client-side screener (DataEngine Cache tabanlı) mimarisinde, screener tablosunun taranıp gösterilebilmesi için ilgili sembollerin `/api/v2/candles` geçmiş verilerinin test ortamında `waitForResponse` ile önceden yüklendiğinden emin olunmalıdır.

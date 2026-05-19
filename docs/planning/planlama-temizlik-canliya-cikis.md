# Planlama — Temizlik ve Canlıya Çıkış

> Aktif referans dosyası. Ana planlarda adı geçen canlıya çıkış hijyeni,
> deployment ve üretim paket kontrol işleri burada takip edilir.
> Güncelleme: 2026-05-19

## Canlı Kritik Düzeltmeler

- [x] Canonical domain kararı `piyasapilotu.com` olarak tekleştirildi.
- [x] Production frontend image'ına nginx SPA fallback config'i eklendi.
- [x] Browser-facing API istekleri `X-API-Key` zorunluluğundan ayrıldı.
- [x] WebSocket API key zorunluluğu `REQUIRE_WS_API_KEY=1` env bayrağına taşındı.
- [x] Nginx genel API rate limit ilk yükleme trafiğine uygun şekilde genişletildi.
- [x] Certbot yenileme sonrası nginx'in yeni sertifikayı okuyabilmesi için periyodik reload eklendi.
- [x] Sembol ve timeframe değişimlerinde URL state senkronizasyonu eklendi.

## Kabul Kontrolleri

- [ ] `https://piyasapilotu.com/` 200 döner.
- [ ] `https://www.piyasapilotu.com/` canonical davranışa göre çalışır veya yönlenir.
- [x] Yerelde `/login`, `/register`, `/pricing`, `/settings`, `/legal/privacy` hard refresh ile 200 döner.
- [x] Yerelde BTCUSDT ve THYAO grafik ekranları `backend HTTP 401/429` göstermeden veri veya bilinçli state gösterir.
- [x] Yerelde Haberler sekmesi skeleton'da kalmaz; misafir kullanıcıya açık `Giriş gerekli` state'i gösterir.
- [x] Yerelde kilitli sekme modalındaki kayıt/plan butonları 404'e gitmez.
- [x] `npm run typecheck`, `npm run build`, `.venv/bin/python -m pytest tests/unit/test_security.py -q` geçer.
- [x] Chrome QA normal profilde yerel ortamda tekrar yapıldı.

## Canlı Deploy Sonrası Tekrar

- [ ] Sunucudaki image/commit hash doğrulanır.
- [ ] Aynı Chrome kabul listesi `https://piyasapilotu.com` üzerinde tekrar koşulur.
- [ ] TLS, redirect, `/api/health` ve SPA route fallback canlı domain üzerinde doğrulanır.

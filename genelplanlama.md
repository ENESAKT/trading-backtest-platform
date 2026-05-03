# GENEL PLANLAMA — PiyasaPilot Yürütme Haritası

> Tek yürütme rehberi. Yeni bir ajan veya yeni oturum önce burayı, sonra ilgili alt planı okur.
> Tarih: 2026-05-02 · Branch: `codex/education-feature-planning`

---

## 0. Ana Kontrol Paneli

Bu bolum projenin tek bakista okunacak yonetim panelidir. Yeni bir AI veya
yeni bir oturum once bu tabloyu okur, sonra `## 0.4 Uygulama Sirasi` altindaki
siraya gore ilgili plan dosyasina gecer.

### 0.1 Yuzde Okuma Kurali

| Alan | Anlam |
|---|---|
| Is yuku payi | Bu planin toplam proje is yuku icindeki agirligi |
| Plan netligi | Planin karar/uygulama detayi ne kadar hazir |
| Tamamlanma | O planin kendi icindeki uygulama gerceklesme orani |
| Agirlikli tamamlanma | `Is yuku payi x Tamamlanma`; toplam proje ilerlemesine katkisi |

Yuzdeler proje yonetimi icin tahmini agirliktir; kesin muhasebe degildir. Bir
faz tamamlandikca bu tablo guncellenir. Yeni bir AI bu yuzdeleri degistirecekse
once ilgili plan dosyasindaki checklistleri ve kod durumunu kontrol eder.

### 0.2 Toplam Durum Ozeti

| Metrik | Deger | Not |
|---|---:|---|
| Toplam uygulama tamamlanma | ~88% | Veri platformu, deploy hijyeni, skill agent, egitim UI eklendi. G1-10 ve B1 eklendi; Backtest B2-13 bekleniyor |
| Kalan uygulama yuku | ~12% | En buyuk kalan is: Backtest Lab detay sprintleri |
| Plan netligi | ~86% | Ana planlar yazildi; bazi uygulama detaylari sprintte netlesecek |
| En kritik sonraki faz | Faz 3 | Backtest Lab (B2, B3, B4...) gelistirmeleri ve G1-10 dogrulamasi |
| Canliya cikis durumu | Iskelet Hazir | Docker-compose.prod ve ilgili temizlik denetimleri kuruldu |
| Veri platformu durumu | Hazir | ClickHouse/MySQL/Redis DB katmanlari mock ve hazirlik asamasinda kuruldu |

### 0.3 Plan Dosyalari, Is Yuku ve Durum

| Sira | Plan dosyasi | Is yuku payi | Plan netligi | Tamamlanma | Agirlikli tamamlanma | Durum | Siradaki ana is |
|---:|---|---:|---:|---:|---:|---|---|
| 0 | `planlama-sprint-gecmis.md` | 30% | 100% | 100% | 30.0% | Tamamlandi | Referans olarak kullan, aktif is yazma |
| 1 | `planlama-veri-platformu.md` | 18% | 90% | 100% | 18.0% | Tamamlandi | Faz 0A: Veri mimarisi ve altyapisi hazirlandi |
| 2 | `planlama-temizlik-canliya-cikis.md` | 10% | 88% | 100% | 10.0% | Tamamlandi | Repo temizligi, docker ignore ve uretim araclari eklendi |
| 3 | `planlama-agent-skill-mentor.md` | 7% | 85% | 100% | 7.0% | Tamamlandi | Skill ve mentor checkleri kuruldu |
| 4 | `planlama-grafik.md` | 10% | 80% | 100% | 10.0% | Tamamlandi | Bütün sprintler G1-G10 tamamlandı (Dogrulama gerekli) |
| 5 | `planlama-backtest.md` | 12% | 82% | 60% | 7.2% | Cekirdek ve B1-B4 tamam, B5 aktif | B5: kalite skoru ve tuzaklar |
| 6 | `planlama-egitimler.md` | 5% | 92% | 100% | 5.0% | UI iskeleti ve icerik eklendi | Dogrula: Egitim kopruleri |
| 7 | `planlama-mali-analiz.md` | 5% | 78% | 5% | 0.3% | Beklemede | Veri platformu ve Borfin/Fastweb on okuma tamamlaninca |
| 8 | `planlama-tasarim.md` | 2% | 95% | 100% | 2.0% | Tamamlandi | Yeni UI isleri gelirse referans |
| 9 | `egitimplanlama.md` | 1% | 90% | 57% | 0.6% | OCR sureci kismi tamam | Mali analiz ve opsiyon/varant/swap kurslarini oku |

Toplam agirlik: **100%**.

### 0.4 Uygulama Sirasi

Bu sira yeni AI icin zorunlu varsayilandir:

1. **Faz 0A — Veri platformu temel kurulum**
   `planlama-veri-platformu.md` VDP-0 -> VDP-4.
   Once plan/docs, sonra ClickHouse/MySQL/Redis dev compose, sema,
   repository ve inventory gelir.

2. **Faz 0B — Repo temizligi ve production paket hijyeni**
   `planlama-temizlik-canliya-cikis.md` RCP-1 -> RCP-3.
   Veri platformu kodu buyumeden `.dockerignore`, artifact ayrimi ve build
   context kontrolu kurulacak.

3. **Faz 0C — Denetim skill'leri ve mentor agent**
   `planlama-agent-skill-mentor.md` ASM-1 -> ASM-4.
   Veri, retention, Borfin temizligi ve deploy kontrolleri script/skill ile
   tekrar calistirilabilir hale gelecek.

4. **Faz 0D — Production deploy hazirligi**
   `planlama-temizlik-canliya-cikis.md` RCP-4 -> RCP-5 ve
   `planlama-veri-platformu.md` VDP-8.
   nginx, domain, TLS, volume, backup, rollback ve `prod-health`.

5. **Faz 1 — Grafik Lab kalan isleri**
   `planlama-grafik.md` G6 -> G10.
   Veri platformu repository katmani oturduktan sonra event marker ve
   timeframe kullanan grafik isleri daha saglam ilerler.

6. **Faz 2 — Backtest Lab ileri isleri**
   `planlama-backtest.md` B1 -> B13.
   Katalog/DSL/gerceklik/kalite/WFA/Monte Carlo/portfoy/paper operasyon.

7. **Faz 3 — Mali Analiz**
   `planlama-mali-analiz.md`.
   Veri platformu, KAP/finansal veri modeli ve Borfin/Fastweb on okuma
   tamamlanmadan kodlanmaz.

8. **Faz 4 — Egitim kopruleri ve yeni icerik**
   `planlama-egitimler.md` ve `egitimplanlama.md`.
   Egitimler v1 tamam; bundan sonrasi urun kopruleri, E2E ve bekleyen kurslar.

### 0.5 Plan Dosyasi Haritasi

| Dosya | Tip | Aktiflik | Ne zaman okunur? |
|---|---|---|---|
| `genelplanlama.md` | Ana yonetim paneli | Aktif | Her oturumun ilk dosyasi |
| `planlama.md` | Plan index'i | Aktif | Dosya haritasi ve karar ozetleri icin |
| `planlama-sprint-aktif.md` | Aktif sprint tablosu | Aktif | Siradaki sprint/adim secimi icin |
| `planlama-veri-platformu.md` | Yeni veri platformu | Aktif/oncelikli | Veri, DB, retention, inventory islerinde |
| `planlama-temizlik-canliya-cikis.md` | Repo/deploy planı | Aktif/oncelikli | Temizlik, Docker, domain, canliya cikis islerinde |
| `planlama-agent-skill-mentor.md` | Skill/agent planı | Aktif/oncelikli | Yeni skill, agent, mentor, denetim scriptlerinde |
| `planlama-grafik.md` | Grafik Lab | Aktif | ChartPanel, indikator, cizim, event marker islerinde |
| `planlama-backtest.md` | Backtest Lab | Aktif | StrategySpec, WFA, Monte Carlo, kalite, optimizer islerinde |
| `planlama-egitimler.md` | Egitimler | Aktif/kismi tamam | Egitim paneli, makale, kopru, Borfin policy islerinde |
| `planlama-mali-analiz.md` | Mali analiz | Beklemede | Veri platformu ve finansal OCR on kosullari tamamlaninca |
| `planlama-tasarim.md` | UI tasarim | Tamamlandi/referans | UI dili bozulursa referans |
| `egitimplanlama.md` | Borfin okuma sureci | Aktif/referans | Yeni kurs okunurken veya artifact temizlenirken |
| `planlama-sprint-gecmis.md` | Tamamlanan sprint arsivi | Referans | Eski is yapildi mi kontrolu icin |
| `ROADMAP.md`, `ILERLEME.md`, `PROJE_DURUM_OZET.md` | Tarihsel snapshot | Referans degil | Sadece gecmis baglam; karar kaynagi degil |

---

## 1. Doğruluk Kaynağı

| Öncelik | Dosya | Rol |
|---:|---|---|
| 1 | `genelplanlama.md` | Hangi sırayla ilerleyeceğimizi söyler |
| 2 | `planlama.md` | Plan dosyalarının index'i |
| 3 | `planlama-sprint-aktif.md` | Aktif fazların kısa takip tablosu |
| 4 | `planlama-veri-platformu.md` | BIST/VIOP veri platformu, ClickHouse/MySQL/Redis, retention ve inventory planı |
| 5 | `planlama-temizlik-canliya-cikis.md` | Repo temizliği, Borfin artifact ayrımı, production package ve deploy planı |
| 6 | `planlama-agent-skill-mentor.md` | Bu konuları denetleyen skill'ler ve mentor/data/release agent planı |
| 7 | `planlama-egitimler.md` | Eğitimler sekmesi ve makale planı |
| 8 | `egitimplanlama.md` | BORFİN okuma kanıtları ve kurs envanteri |
| 9 | `planlama-backtest.md`, `planlama-grafik.md`, `planlama-mali-analiz.md` | Alan planları |

`ROADMAP.md`, `ILERLEME.md` ve `PROJE_DURUM_OZET.md` tarihsel snapshot kabul edilir; güncel sprint kararı için kullanılmaz.

---

## 2. Borfin İçerik Uygunluk Kararı

BORFİN arşivi ürün için uygun, ama doğrudan içerik kaynağı değil; kavram ve iş akışı kaynağıdır.

| Alan | Karar | Gerekçe |
|---|---|---|
| Eğitimler sekmesi | Uygun | Kavramlar özgün PiyasaPilot makalelerine dönüştürülebilir |
| Grafik Lab | Uygun | Trend, kanal, Fibonacci, formasyon ve gösterge kavramları grafik araçlarına bağlanabilir |
| Backtest Lab | Çok uygun | Algo trade, WFA, Monte Carlo, System Tester, Explorer ve rapor kavramları ürün çekirdeğiyle örtüşüyor |
| VIOP/Vadeli | Uygun ama kapılı | Veri/lisans/kontrat varsayımları olmadan gerçek işlem veya paper aksiyonu açılmamalı |
| Mali Analiz | Beklemeli | İlgili temel/mali analiz kursları henüz OCR ile okunmadı; plan şimdilik taslak |
| Opsiyon/Varant/Swap | Beklemeli | 33 video okunmadan yalnızca gelecek modül ve risk uyarısı seviyesinde kalmalı |
| Platform eğitimleri | Kısıtlı | Finnet/Fastweb/Stockeys gibi ürün ekranları kopyalanmaz; sadece ihtiyaç listesi çıkarılır |

Yasaklar: Borfin ekran görüntüsü, marka dili, uzun metin, telifli formül, yardımcı dosya içeriği ve kurs slaytları birebir ürüne taşınmaz.

---

## 3. Borfin Okuma Durumu

Toplam arşiv: 26 kurs klasörü, 825 video.

| Durum | Kurs | Video | Not |
|---|---:|---:|---|
| Tamamlandı | 9 | 469 | Frame OCR + bazı yardımcı dosya metinleri |
| Bekliyor | 17 | 356 | Önce finansal analiz ve opsiyon/varant/swap dilimleri okunacak |

Okuma yöntemi şu an ses transkripti değil, macOS AVFoundation + Vision frame OCR. Bu nedenle ekranda görünmeyen konuşma detayları eksik olabilir. İçerik makalelerine `source_confidence`, `source_method` ve `needs_audio_transcript` alanları konacak.

---

## 4. Uygulama Sırası

### 0. Veri platformu ve üretim hazırlığı

- [ ] `planlama-veri-platformu.md` ana veri kararı olarak uygulanacak: BIST 100 + VIOP öncelik, ClickHouse/MySQL/Redis, inventory, retention ve timeframe graph.
- [ ] BIST hisse `1m` verisi yalnızca son 1 yıl tutulacak; VIOP `1m` verisi 10 yıl hedefleyecek.
- [ ] BIST hisselerde `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`, `1y` için 10 yıl hedeflenecek.
- [ ] Günlükten dakikalık veri üretilmeyecek; sadece küçük timeframe'den büyük timeframe'e rollup yapılacak.
- [ ] `planlama-temizlik-canliya-cikis.md` uygulanmadan canlıya çıkılmayacak: artifact/cache/local DB production image'a girmeyecek.
- [ ] `planlama-agent-skill-mentor.md` içindeki denetim skill'leri ve mentor agent planı, veri/deploy fazlarını kontrol edecek şekilde eklenecek.

### 1. Git ve repo hijyeni

- [x] `artifacts/` git dışına alınacak.
- [x] Yerel SQLite çalışma veritabanları git dışına alınacak.
- [x] Tracked olan `data/strategy_lab/strategies.sqlite3` index'ten çıkarıldı; lokal dosya olarak korunuyor.
- [ ] Commitler path bazlı yapılacak; artifact, cache, lokal DB ve kişisel memory dosyaları commitlenmeyecek.
- [ ] `repo-cleanup-report`, `borfin-integration-check` ve `production-package-check` komutları eklendikten sonra canlı paket temizliği doğrulanacak.

### 2. Eğitim kaynak modelini sabitle

- [x] `planlama-egitimler.md` içindeki makale listesi OCR kanıtı ve güven notuyla eşleşecek.
- [x] Her makale frontmatter'ına kaynak kurs, yöntem ve güven alanı eklenecek.
- [x] Borfin OCR'da açık kanıtı olmayan `VWAP` başlığı Eğitimler v1 listesinden çıkarıldı; yerine OCR'da görülen hacim indikatörleri kullanıldı.
- [ ] Borfin artifact temizliği öncesi `borfin-integration-auditor` kontrolü yapılacak; ham OCR/frame/video dosyaları urune runtime bağımlılığı olarak kalmayacak.

### 3. Eğitimler sekmesi altyapısı

- [ ] Klavye sırası korunacak: Sinyaller `5`, Eğitimler `6`, Mali Analiz `7`.
- [x] `EgitimlerPanel.ts` ve içerik klasörleri eklenecek.
- [x] İlk sürümde güvenli markdown render, kategori, arama ve köprü aksiyonları olacak.
- [x] İlk içerik dalgası: Bollinger, RSI, MACD, SMA/EMA, ATR.

### 4. Grafik ve eğitim köprüleri

- [ ] Eğitim makalesinden grafiğe indikatör ekleme.
- [ ] Formasyon/Fibonacci yazılarından ilgili çizim aracına köprü.
- [ ] Risk uyarısı: gecikme, repaint, yanlış teyit, düşük hacim.

### 5. Backtest Lab düzeltme

- [x] `planlama-backtest.md` mevcut yapılmış altyapı ve kalan işler diye ayrıldı.
- [ ] StrategySpec/short/report archive/CSV/optimizer gibi mevcut işler tekrar yapılacak gibi gösterilmeyecek.
- [ ] Kalan ağır işler: WFA modülü, Monte Carlo, kalite skoru, stabil optimizasyon, portföy lab.

### 6. Mali Analiz önce okuma, sonra kod

- [ ] Cahit Yılmaz Mali Analiz Teknikleri, Temel Analiz, Üzeyir Doğan, Firma Değerleme ve Fastweb/Finnet eğitimleri önce OCR'dan geçirilecek.
- [ ] Sonra `planlama-mali-analiz.md` oran seti, veri şeması ve API kontratı yeniden netleştirilecek.
- [ ] BIST 30 listesi statik yazılmayacak; uygulamadaki sembol kaynağı veya sağlayıcıdan üretilecek.

### 7. VIOP ve türevler

- [ ] Vadeli/VOB planı sadece gerçek veri/kontrat varsayımı kapılarıyla ilerleyecek.
- [ ] Opsiyon/Varant/Swap kursları okunduktan sonra eğitim makalelerine ve risk uyarılarına bağlanacak.

---

## 5. Kabul Kapıları

- Plan değişikliği: ilgili `.md` dosyasında durum ve kaynak notu güncellenir.
- Kod değişikliği: en dar ilgili test çalıştırılır.
- Frontend değişikliği: ilgili E2E veya en azından build kontrolü yapılır.
- Eğitim içeriği: Borfin'den birebir kopya yok, kaynak yöntemi ve güven notu var.
- Veri platformu değişikliği: `data-inventory-check`, `data-retention-guardian` ve `timeframe-derivation-check` mantığına uyulur.
- Canlıya çıkış değişikliği: `production-package-check` ve `deployment-check` temiz olmadan deploy yapılmaz.
- Git: artifact/cache/sqlite yok; commit tek konuya ait; push sonrası branch durumu temiz veya bilinçli artıklarla raporlanır.

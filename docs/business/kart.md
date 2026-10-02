# Backtest (PiyasaPilot) — İş Kartı

## Bir cümlede

Bireysel yatırımcı ve trader'lar için, **piyasa verisini toplayıp strateji tarayan, kâğıt üzerinde işlem yapan ve stratejileri geçmiş veriyle tekrarlanabilir şekilde test eden** platform.

---

## Temel bilgiler

| Alan | Değer |
|------|-------|
| Proje klasörü | `../../../Backtest/` |
| Teknoloji | Python 3.12 + FastAPI, MySQL, ClickHouse, Redis, Vite web istemci, Flutter mobil, Docker Compose, GitHub Actions + Trivy |
| Olgunluk | 🟢 En olgun proje — 230+ görev, 117/117 test geçiyor, CI kurulu |
| Aktif mi | ⬜ Karar verilmedi |
| Teknik doküman | `Backtest/README.md`, `YAPILANLAR.md`, `CANLIYA_ALMA_REHBERI.md` |

---

## Müşteri

| Alan | Değer |
|------|-------|
| Kim | Bireysel yatırımcı, teknik analizle çalışan trader, strateji geliştirmek isteyen yazılımcı |
| Hangi acısı var | Strateji fikri var ama geçmişte işe yarayıp yaramadığını test edemiyor; Excel'de yapmaya çalışıyor |
| Şu an nasıl çözüyor | TradingView (pahalı, sınırlı backtest), Excel, ya da hiç test etmeden işlem yapma |
| Neden bunu kullansın | Tekrarlanabilir backtest + tarama + kâğıt üzerinde işlem tek yerde, Türkiye piyasasına uygun |
| Nerede bulunur | Ekşi/Reddit borsa toplulukları, YouTube trading kanalları, Twitter finans, Telegram grupları |

---

## Gelir modeli

| Alan | Değer |
|------|-------|
| Model | Kademeli aylık abonelik (ücretsiz / pro) |
| Fiyat | ❓ |
| Değişken maliyet | Piyasa verisi sağlayıcı lisansı + ClickHouse depolama |
| Brüt marj | ❓ |

⚠️ **Veri lisansı kritik:** Borsa verisi çoğu zaman ücretsiz dağıtılamaz. Hangi verinin ticari olarak yeniden dağıtılabildiği netleşmeden ücretli satış yapılamaz.

---

## Rekabet

| Rakip | Fiyat | Farkımız |
|-------|-------|----------|
| TradingView | ❓ | Türkiye piyasası odağı, gerçek backtest motoru |
| ❓ yerli rakipler | | |

---

## Canlıya çıkmak için eksikler

- [ ] Piyasa verisi lisans durumu netleştir (**bloke edici**)
- [ ] Yasal uyum → `Backtest/YAPILACAKLAR_YASAL_UYUM.md`
- [ ] Kişisel veri envanteri → `Backtest/KISISEL_VERI_ENVANTERI.md`
- [ ] "Yatırım tavsiyesi değildir" konumlandırması ve sorumluluk metinleri
- [ ] Ödeme entegrasyonu
- [ ] Canlıya alma → `Backtest/CANLIYA_ALMA_REHBERI.md`
- [ ] Fiyatlandırma kararı

---

## Riskler

| Risk | Etki | Ne yapılacak |
|------|------|--------------|
| **Yatırım tavsiyesi / SPK sınırı** | 🔴 Yüksek | Ürün "araç"tır, sinyal/tavsiye vermez. Konumlandırma ve metinler buna göre. Hukuki görüş alınmalı. |
| **Veri lisansı** | 🔴 Yüksek | Sağlayıcı sözleşmesi okunmadan ticari sunum yapma |
| Yoğun rekabet | 🟡 Orta | Niş: Türkiye piyasası + gerçek backtest |
| Altyapı maliyeti (ClickHouse, veri) | 🟡 Orta | Gelir öncesi sabit gider yüksek |

---

## Not

Teknik olarak en hazır proje ama **yasal olarak en yüklü** olanı. Şirket kurulmadan ve hukuki çerçeve netleşmeden ücretli satışa açılmamalı. Bu yüzden portföy önceliğinde 3. sırada — teknik hazırlığı değil, hazırlık yükü sıralamayı belirliyor.

---

## Durum

| Tarih | Ne oldu |
|-------|---------|
| 2026-08-06 | İş kartı oluşturuldu. |

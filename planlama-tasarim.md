# Tasarım ve UI Revizyon Planı — PiyasaPilot

> Bu dosya, uygulamanın ana yapısını (DOM/bileşen hiyerarşisini) bozmadan arayüzü daha modern, okunaklı ve "premium" hale getirme adımlarını içerir.
> Tarih: 2026-05-02

---

## 1. Mevcut Tasarım Analizi ve Sorunlar

Mevcut arayüz işlevsel olarak çalışsa da görsel olarak bazı eksiklikler barındırmaktadır:
- **Bilgi Yoğunluğu (Clutter):** Menülerde (özellikle Grafik araç çubuğunda ve Strateji sayfasında) çok fazla öğe yan yana sıkıştırılmış durumda.
- **Tipografi ve Okunabilirlik:** Yazı tipleri (9px, 10px, 11px) modern ekranlar için çok küçük. Uzun süreli kullanımlarda göz yoruyor.
- **Boşluk (Whitespace) Eksikliği:** Padding ve margin değerleri çok düşük (`padding: 2px 7px` gibi), bu da arayüzün nefes almasını engelliyor.
- **Renk Paleti (GitHub Dark):** Mevcut palet (bg: `#0d1117`, panel: `#161b22`) kod editörü için iyi olsa da, premium bir finans terminali hissiyatından ziyade teknik bir görünüm veriyor.

---

## 2. Çözüm Stratejisi (Ana Yapıyı Bozmadan)

HTML yapısını (`app.ts` veya komponent içi DOM ağacı) radikal şekilde değiştirmeden, **sadece CSS, stil değişkenleri ve ufak DOM sınıf değişiklikleriyle** şu hedeflere ulaşılacak:

1. **Premium Dark Mode:** Renk paletini daha sofistike bir koyu temaya geçirmek (örneğin arka plan için derin bir "slate/obsidian", vurgular için daha canlı neon mavi/yeşil/kırmızı).
2. **Tipografi Güncellemesi:** Temel font boyutunu büyütmek (min 11px, temel 13px/14px). Menü başlıklarında daha modern ağırlıklar kullanmak.
3. **Daha Büyük Tıklama Alanları:** Butonlar ve inputlar için padding değerlerini artırmak, "touch-friendly" ve estetik oranlar yakalamak.
4. **Bölümlendirme (Hierarchy):** Paneller arasına daha belirgin görsel hiyerarşi (subtle box-shadow, glassmorphism veya belirgin border) eklemek.
5. **Yuvarlatılmış Köşeler (Border Radius):** Köşeleri biraz daha yuvarlatarak (örn: 6px → 8px) daha yumuşak bir arayüz sunmak.

---

## 3. Yeni Renk ve Tipografi Paleti Önerisi

**Tipografi:**
- Font: `Inter`, `Roboto` veya `Outfit` (varsayılan sans-serif için). Mono için `JetBrains Mono` veya `Fira Code` korunabilir.

**Renk Paleti (Örnek Revizyon):**
- `--bg`: `#0b0e14` (Daha derin ve soğuk bir siyah)
- `--panel`: `#12161f` (Arka plandan hafifçe ayrışan lacivert-gri)
- `--panel2`: `#181d29` (Hover ve ikinci katman)
- `--border`: `#222834`
- `--border2`: `#2a3241`
- `--text`: `#94a3b8` (Slate 400 - Daha okunaklı gri)
- `--text-bold`: `#f1f5f9` (Slate 100 - Net beyaz/gri)
- `--blue`: `#3b82f6` veya `#60a5fa` (Premium Mavi)
- `--green`: `#10b981` (Daha parlak zümrüt yeşili)
- `--red`: `#ef4444` (Canlı ve uyarıcı kırmızı)
- `--yellow`: `#f59e0b`

---

## 4. Geliştirme Fazları ve Adımları

Bu revizyon işleri `style.css` ve ilgili komponent içi CSS değişkenlerinde (`ChartPanel.ts` vb.) yapılacaktır.

| Adım | İş | Etki Alanı | Durum |
|------|----|------------|-------|
| T1 | **Renk Paleti Değişimi:** `:root` içerisindeki `--bg`, `--panel`, `--text` vb. renklerin yeni premium paletle değiştirilmesi. | Tüm Uygulama (`style.css`, `ChartPanel.ts`) | Bekliyor |
| T2 | **Tipografi İyileştirmesi:** Base font boyutlarının artırılması. 9px/10px olan yerlerin 11px/12px'e, 11px/12px olan yerlerin 13px/14px'e çekilmesi. | Tüm Uygulama | Bekliyor |
| T3 | **Boşluk (Spacing) Ayarları:** `.ctrl-btn`, `input`, `td`, `th` padding değerlerinin artırılması. Flex `gap` değerlerinin 2px/4px'ten daha geniş değerlere çekilmesi. | Layout, Butonlar, Tablolar | Bekliyor |
| T4 | **Grafik Toolbar Düzenlemesi:** `.chart-controls` içindeki aşırı sıkışıklığı gidermek için butonlara arka plansız (sadece hover'da beliren) stiller veya gruplama verilmesi. | Grafik Paneli | Bekliyor |
| T5 | **Strateji Paneli Formları:** Strateji sayfasındaki lab formları ve inputların border-radius, padding ve border renklerinin yumuşatılması. | Strateji Lab | Bekliyor |
| T6 | **Scrollbar ve Hover Efektleri:** Scrollbar'ların gizlenmesi veya inceltilip temaya uydurulması. Tablo ve listelerde hover efektlerinin (glow/opacity) eklenmesi. | Genel UX | Bekliyor |

---

## 5. Kabul Kriterleri

1. Arayüzün HTML yapısı bozulmamalı, React/TypeScript/Vanilla JS içindeki mantık değişmemeli.
2. Renk kontrast oranları WCAG standartlarına yakın, göz yormayan bir yapıda olmalı.
3. Uygulama, mevcut durumda olduğu gibi karanlık (dark mode) hissini korurken, daha ferah görünmeli.
4. E2E testleri (örneğin elementlerin `visible` olması) margin/padding değişikliklerinden etkilenmemeli (boyut değişimleri taşma yapmamalı).

# Tasarım ve UI Revizyon Planı — PiyasaPilot v2.1 (Premium Terminal)

> Bu dosya, uygulamanın HTML/DOM hiyerarşisini (yapısını) bozmadan, modern finansal terminallerin (ör: Hyperliquid, Tensor, modern TradingView temaları) sunduğu "Premium" ve "Akıcı" deneyimi yakalamak için izlenecek CSS ve UX adımlarını detaylandırır.
> Tarih: 2026-05-02

---

## 1. Vizyon ve Hedef ("Wow" Faktörü)

Kullanıcıların piyasa pilotunu ilk açtığında karşılaşacağı hissiyat, klasik bir kod editörü (GitHub dark mode) olmaktan çıkıp, **hızlı, akıcı, odaklanmayı kolaylaştıran yüksek yoğunluklu (high-density) premium bir işlem laboratuvarı** olmalıdır.

Bunu sağlarken ana kuralımız: **Hiçbir `app.ts`, `ChartPanel.ts` veya `MaliAnalizPanel.ts` DOM yapısını bozmak yok.** Sadece CSS sınıflarını (gerekirse JS içindeki class tanımlarını) ve `style.css` dosyasını güncelleyeceğiz.

---

## 2. Modern UI / UX Prensipleri ve Çözümler

### A. Tipografi ve Rakamların Okunabilirliği
- **Tabular Numaralar:** Fiyatlar, yüzdeler ve K/Z durumları sürekli değişir. Rakamların titremesini önlemek için CSS'te `font-variant-numeric: tabular-nums;` kullanılacak.
- **Font Seçimi:** Arayüz metinleri için **Inter** veya **Outfit**, rakamlar ve kod/formül alanları için **JetBrains Mono** kullanılacak.
- **Boyutlar:** 9px - 10px gibi göz yoran boyutlar terk edilecek. Min: `11px`, Temel: `13px`.

### B. Renk ve Işık (Glassmorphism & Glow)
- **Mat Arka Planlar:** Keskin `#000` veya `#0d1117` yerine, daha soft ve derin olan "Obsidian" (`#0A0E17`) veya "Midnight Slate" kullanılacak.
- **Micro-Glow Efektleri:** Aktif stratejiler, kârda olan pozisyonlar veya açık indikatör butonları sadece renk değiştirmeyecek, hafif bir `box-shadow` (glow) ile vurgulanacak.
- **Blur (Buzlu Cam):** Tooltipler, dropdown menüler ve yüzen (floating) bilgi kutuları (`.chart-info-overlay`) `backdrop-filter: blur(12px)` ile arka planı hafifçe flulaştırarak modern bir his verecek.

### C. Yoğun Veri ve Kalabalık Menü Yönetimi (Clutter Reduction)
- **Hap (Pill) Tasarımlar:** Grafik araç çubuğundaki (1D, 1H, BB, RSI vb.) kalabalık butonlar, köşeleri yuvarlatılmış hap (pill) tasarımlara çevrilecek.
- **Sınır (Border) Temizliği:** Her butonun etrafındaki kutu çizgileri (border) kaldırılacak. Bunun yerine butonlar sadece `hover` veya `active` durumundayken hafif bir arka plan rengi kazanacak. Bu, arayüzdeki "çizgi kirliliğini" (border noise) yok eder.
- **Kaydırılabilir (Scrollable) Alanların İyileştirilmesi:** Kaydırma çubukları ince (thin) ve temaya uygun, şeffaf hale getirilecek.

---

## 3. Yeni Premium Renk Paleti (CSS Variables)

```css
:root {
  /* Temel Arka Planlar (Derin, göz yormayan) */
  --bg:           #0B0E14; /* Ana arka plan */
  --panel:        #131722; /* Panel arka planı */
  --panel-hover:  #1C2130;
  
  /* Kenarlıklar (Çok daha şeffaf ve zarif) */
  --border:       rgba(255, 255, 255, 0.08);
  --border-focus: rgba(59, 130, 246, 0.5);
  
  /* Metin Renkleri */
  --text-dim:     #64748B; /* Önemsiz metinler */
  --text:         #94A3B8; /* Standart metinler */
  --text-bold:    #F8FAFC; /* Başlık ve önemli veriler */
  
  /* Vurgu ve İşlem Renkleri (Daha canlı ve neon) */
  --blue:         #3B82F6; /* Vurgu Rengi */
  --blue-glow:    rgba(59, 130, 246, 0.15);
  --green:        #10B981; /* Alış / Kâr */
  --green-glow:   rgba(16, 185, 129, 0.15);
  --red:          #EF4444; /* Satış / Zarar */
  --red-glow:     rgba(239, 68, 68, 0.15);
  --yellow:       #F59E0B; /* Uyarı / Favori */
}
```

---

## 4. Geliştirme Fazları (Adım Adım CSS/UI Değişimi)

| Faz | Odak Alanı | Uygulanacak Spesifik CSS/UI Kararları | Durum |
|-----|------------|-----------------------------------------|-------|
| **F1** | **Global Renk & Tipografi** | `:root` değişkenlerinin güncellenmesi. `Inter` fontunun eklenmesi. `tabular-nums`'ın aktif edilmesi. İnce ve gizli scrollbar yapısına geçilmesi. | Tamamlandı |
| **F2** | **Grafik Toolbar (Top Bar) Temizliği** | `.chart-controls` içindeki butonların border'larının silinmesi, sadece hover'da belirginleşmesi. Aktif öğelere hafif glow (`box-shadow`) eklenmesi. Gap değerlerinin `2px`'ten `6px`'e çıkartılması. | Tamamlandı |
| **F3** | **Panel & Kart Hiyerarşisi** | `.panel-section`, `.wallet-card`, `.strategy-card` gibi alanların border'larının inceltilmesi. Köşe yuvarlamalarının (border-radius) `8px`'e çekilmesi. Hover durumlarında kartların hafif yukarı kalkması (`transform: translateY(-1px)`) veya aydınlanması. | Tamamlandı |
| **F4** | **Form ve Input Estetiği** | `.form-row input`, `select` ve `textarea`'ların iç padding'lerinin büyütülmesi (örn: `8px 12px`). Focus anında sert border yerine zarif bir mavi focus ring (`box-shadow: 0 0 0 2px var(--border-focus)`) verilmesi. | Tamamlandı |
| **F5** | **Cam Efektleri (Glassmorphism)** | `.chart-info-overlay`, `.indicator-center` ve açılır menülere `backdrop-filter: blur(12px)` ve `background: rgba(19, 23, 34, 0.8)` uygulanması. | Tamamlandı |
| **F6** | **Tablo ve Liste İyileştirmeleri** | İşlem geçmişi ve sembol listelerindeki satır aralıklarının (line-height ve padding) açılması. Kâr/Zarar hücrelerine `tabular-nums` ve pozitif/negatif renk atamalarının vurgulanması. | Tamamlandı |
| **F7** | **Çoklu Ölçek (Multi-Scale) ve Karşılaştırma Modülü** | Karşılaştırma olarak eklenen sembollerin grafiği ezercesine sağ Y eksenini kullanması iptal edilecek. Ana grafik sağ eksende, karşılaştırma grafiği sol (Left Y-Axis) eksende izole gösterilecek. Karşılaştırma renklerinin anlık değişimi için ufak bir renk seçici aracı eklenecek. | Tamamlandı |

---

## 5. Uygulama Kuralları ve Kabul Kriterleri

1. **Sıfır Yapısal Hasar:** Mevcut `.ts` ve `.html` içindeki etiket yapısı (div iç içeliği) asla bozulmayacak. Yeni div eklenmeyecek, silinmeyecek. Yalnızca class isimleri değiştirilebilir veya yeni css kuralları yazılabilir.
2. **Kullanışlılık (Usability):** Hedef kitlenin traderlar olduğu unutulmamalıdır. Alanlar çok ferah yapılarak ekrandaki veri yoğunluğu kaybettirilmeyecektir. Yalnızca "gürültü" (kalın çizgiler, zıt renkler) temizlenecek, veriler "tabular" fontlarla ön plana çıkartılacaktır.
3. **Performans:** Sık değişen grafik üzeri öğelerde (crosshair info vb.) ağır gölge ve blur efektleri ölçülü kullanılacak, Chart.js ve Lightweight Charts'ın canvas performansını etkilememesine dikkat edilecektir.

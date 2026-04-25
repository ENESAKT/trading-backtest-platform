# Öğrenilenler — Quant Engine

## Mimari Kararlar

- **ClickHouse yerine DuckDB + Parquet tercih edildi.** Tek kullanıcılı yerel sistemde sunucu-tabanlı DB gereksiz. DuckDB embedded çalışır, zero-copy okuma yapar ve kurulum `pip install duckdb` kadar basit. Performans tek kullanıcıda eşdeğer hatta daha iyi (network serialization yok).

- **Polars birincil DataFrame kütüphanesi olarak seçildi.** Pandas'a göre 3-100x daha hızlı, tüm CPU çekirdeklerini otomatik kullanır, Apache Arrow formatında çalışır. Pandas ekosistem uyumu için yedek olarak tutulur.

- **TA-Lib yerine pandas-ta kullanılacak.** TA-Lib'in macOS/Apple Silicon kurulumu sorunlu (C derlemesi gerekiyor). pandas-ta saf Python, pip ile sorunsuz yüklenir.

## Veri Kaynakları

- **Yahoo Finance BIST verileri için `.IS` suffix gerekli.** Örn: `THYAO.IS`. Veri kalitesi %100 güvenilir değil — özellikle split/temettü düzeltmeleri hatalı olabilir. KAP'tan cross-check önerilir.

- **VİOP tick verisi ücretsiz kaynaklarda bulunmuyor.** Borsa İstanbul resmi veri satışı veya dxFeed gibi ücretli servisler gerekli. İlk fazda sadece BIST hisse verisi ile çalışılacak.

## Ortam ve Kurulum

- **Python 3.11.15 Homebrew üzerinden mevcut** (`/opt/homebrew/bin/python3.11`). Sanal ortam bu sürümle oluşturuldu.

- **İnternet bağlantısı olmadan paketler yüklenemedi.** Bağlantı geldiğinde `source .venv/bin/activate && pip install -r requirements.txt` komutu ile tek seferde kurulum yapılacak.

## Backtest Motor Tasarımı

- **Execution semantics spec zorunlu.** "Bar kapanışında sinyal üret, bir sonraki bar açılışında execute et" gibi net kural olmadan backtest sonuçları "varsayım başarısı" olur, "strateji başarısı" değil. Intrabar ambiguity, fill policy ve order type desteği tanımlanmalı.

- **Veri katmanı 4 seviyeye ayrılmalı:** raw → clean → adjusted → feature. Her transform için lineage metadata tutulmalı. Aksi halde birkaç ay sonra hangi veri ne kadar işlenmiş karışır.

- **VİOP ayrı bir çekirdek mantık gerektirir.** Hisse backtest'ini genişletmek yetmez. Contract multiplier, tick size/value, margin, settlement, rollover, forced liquidation ayrı modül.

- **Point-in-time integrity en tehlikeli hata kaynağı.** Feature timestamp ≤ decision timestamp < execution timestamp zinciri zorunlu. Warm-up bars standardı konulmalı (varsayılan 200 bar).

- **Experiment tracking olmazsa 2 ay sonra "hangi ayarla bu sonucu almıştım?" kabusu başlar.** Her koşu için run_id, config snapshot, git hash, data hash, random seed kaydedilmeli.

- **Optimizasyon governance kuralları şart.** Sadece en yüksek Sharpe'ı almak overfit garantisi. Out-of-sample performans, parameter stability, turnover cezası, cost robustness birlikte değerlendirilmeli.

## Kod Kalitesi ve Süreç

- **Kodu yazdıktan sonra kendi bug'larını denetle.** İlk sprint'te 4 bug fark edilmeden bırakıldı: append tüm dosyayı okuyor, paralel fetch çalışmıyor, Polars hiç kullanılmamış, Parquet yazımı atomic değil. "Yazdım bitti" değil "yazdım test ettim doğruladım bitti" olmalı.

- **Önce motor doğru hesaplasın, sonra güzel görünsün.** UI planlamak erken aşamada dikkat dağıtıyor. Strateji sonuçlarının doğruluğu kanıtlanmadan arayüze geçmek, yanlış sonuçları güzel göstermek demek.

- **"Alttan yukarı" düşün, "üstten aşağı" değil.** Modül listesi yazmak kolay, ama "bu satır gerçekten doğru mu?" sorusunu sormak zor. Golden fixture + invariant testler olmadan motorun doğruluğu kanıtlanamaz.

- **Detaylı code review 45 sorun ortaya çıkardı.** İlk yazdığım kodda SQL injection riski (`storage_manager.py` f-string ile SQL oluşturma), veri uydurma riski (`auto_fix()` sınırsız ffill), filesystem mutation on read (`_symbol_path()` her çağrıda mkdir), geçersiz mode parametresinin sessizce kabul edilmesi (`mode="nonsense"`), timezone bilgisinin silinmesi (`tz_localize(None)`) gibi ciddi sorunlar vardı. Bunların hiçbirini yazdığım an fark etmedim. Ders: kod yazdıktan sonra her fonksiyonu "bu nasıl kötüye kullanılabilir?" gözüyle oku.

- **yfinance `end` parametresi exclusive (dışlayıcı) çalışıyor.** `end="2024-01-15"` derseniz 15 Ocak dahil olmaz. BIST kapanış sonrası çağırırken bugünün verisini kaçırmamak için `end = tomorrow` kullanılmalı.

- **`pandas-ta>=0.3.14b1` pip'te bulunamıyor.** Ya `pandas-ta-classic` paketine geçmeli, ya da indikatörleri doğrudan NumPy/Polars ile kendimiz yazmalıyız. İkinci seçenek daha iyi çünkü dış bağımlılığı azaltır.

- **Bağımlılıkları `>=` ile serbest bırakmak tehlikeli.** Major versiyon atlaması API kırılmasına neden olabilir. `pip-tools` veya `uv.lock` ile sürüm sabitlenmeli.

## Mimari Yeniden Yapılanma

- **"Modüler monolit + temiz çekirdek" kararı alındı.** Core katmanı (order, fill, portfolio, clock) hiçbir dış bağımlılığı (yfinance, Streamlit, DuckDB) bilmemeli. Bağımlılık akışı tek yönlü: `core ← data ← strategy ← backtest ← research ← reporting ← app`. Tersi asla olmamalı.

- **Interface/Protocol pattern zorunlu.** `DataProvider`, `StorageBackend`, `Strategy`, `ExecutionModel`, `CostModel` soyut arayüzleri tanımlanacak. Böylece yeni veri kaynağı, yeni strateji veya yeni UI eklerken motor bozulmaz.

- **Referans projeler incelendi.** VectorBT'den vektörize hız, Backtrader'dan strategy/indicator yapısı, LEAN'den katman ayrımı, Freqtrade'den reproducibility, Backtesting.py'den basit API dersleri alınacak. Hiçbirinin tamamı kopyalanmayacak.

- **orders.parquet ve fills.parquet ayrı olmalı.** Sadece trades.parquet yetmez. Emir verme anı ile dolum anı farklı veriler taşır (slippage, partial fill, rejected order). Audit trail bunların hepsini zincirlemeli.

- **UI grafik performansı için downsample şart.** 10K+ bar'ı tarayıcıya ham göndermek sayfayı kilitler. Resample/downsample yapılmalı. Matrix ekranında da her hücreyi canlı hesaplama yerine snapshot tablo üretilip UI onu okumalı.

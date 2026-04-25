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

---
name: "source-command-durum"
description: "Tüm servislerin durumunu raporla"
---

# source-command-durum

Use this skill when the user asks to run the migrated source command `durum`.

## Command Template

# /durum

Tüm PiyasaPilot servislerini kontrol et ve durumu raporla.

## Adımlar

1. **Gateway Health:**
   ```bash
   curl -s http://localhost:8000/api/health | python -m json.tool
   ```

2. **Cache Durumu:** Health response'undan:
   - Toplam bar sayısı
   - Farklı sembol sayısı
   - Son veri zamanı

3. **Worker Durumu:** Health response'undan:
   - Binance WS: bağlı mı, iteration sayısı
   - Yahoo poller: çalışıyor mu, son hata
   - BIST poller: çalışıyor mu, son hata

4. **Paper Trading Durumu:**
   ```bash
   curl -s http://localhost:8000/api/paper/wallets | python -m json.tool
   ```
   - Aktif strateji sayısı
   - Dondurulmuş strateji sayısı
   - Toplam açık pozisyon

5. **Signal Generator:** Health response'undan:
   - Aktif strateji listesi
   - Üretilen sinyal sayısı

## Çıktı Formatı

```
## PiyasaPilot Durum Raporu — [tarih saat]

### 🟢 Gateway: Çalışıyor (v2.0.0)

| Bileşen | Durum | Detay |
|---------|-------|-------|
| API | ✅ | Port 8000, read-only |
| Cache | ✅ | X bar, Y sembol |
| Binance WS | ✅ | Z iterasyon |
| Yahoo Poller | ✅ | — |
| BIST Poller | ✅ | — |
| Signal Generator | ✅ | N strateji aktif |
| Paper Executor | ✅ | M sinyal işlendi |

### Paper Trading
- Aktif cüzdan: X
- Toplam equity: ₺XX.XXX
```

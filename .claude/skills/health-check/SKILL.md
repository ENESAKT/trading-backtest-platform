# Health Check

Tüm PiyasaPilot servislerini kontrol et ve durumu raporla.

## Kullanım

Bu skill, sistemin sağlığını kontrol etmek için çağrılır.

## Kontrol Komutları

```bash
# 1. Gateway
curl -sf http://localhost:8000/api/health | python3 -m json.tool

# 2. Cache boyutu
curl -sf http://localhost:8000/api/health | python3 -c "
import sys, json
h = json.load(sys.stdin)
c = h['cache']
print(f'Cache: {c[\"rows\"]} bar, {c[\"distinct_symbols\"]} sembol')
print(f'Son veri: {c[\"last_inserted_at\"]}')
print(f'Workers: {len(h[\"workers\"])} aktif')
for w in h['workers']:
    print(f'  - {w[\"name\"]}: iter={w.get(\"iterations\",\"?\")} err={w.get(\"last_error\",\"-\")}')
"

# 3. Paper trading
curl -sf http://localhost:8000/api/paper/wallets | python3 -c "
import sys, json
d = json.load(sys.stdin)
wallets = d.get('wallets', [])
print(f'Paper trading: {len(wallets)} cüzdan')
for w in wallets:
    status = '🔴 DONDURULDU' if w['is_halted'] else '🟢 Aktif'
    pnl = w['cash'] - w['initial_capital']
    print(f'  {w[\"strategy_id\"]}: {status} | Nakit: {w[\"cash\"]:.2f}₺ | PnL: {pnl:+.2f}₺')
"

# 4. WebSocket test (5 saniyelik)
timeout 5 wscat -c ws://localhost:8000/ws/quotes 2>/dev/null || echo "WS test: wscat kurulu değil veya bağlantı yok"
```

## Sağlık Kriterleri

| Bileşen | Sağlıklı | Uyarı | Kritik |
|---------|----------|-------|--------|
| Gateway | 200 OK | — | Bağlantı yok |
| Cache | >1000 bar | <100 bar | 0 bar |
| Workers | 3/3 aktif | 1 hatalı | 2+ hatalı |
| Son veri | <5 dk | <30 dk | >1 saat |

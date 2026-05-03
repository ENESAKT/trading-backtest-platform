# Deploy Stack

Docker Compose ile servisleri başlat/durdur ve healthcheck yap.

## Kullanım

Altyapı deployment ve yönetimi için çağrılır.

## Komutlar

```bash
# Servisleri başlat
cd /Users/enes/AgentWorkspace/Backtest
docker-compose up -d

# Durumu kontrol et
docker-compose ps

# Logları izle
docker-compose logs --tail 50 api
docker-compose logs --tail 50 workers

# Belirli servisi yeniden başlat
docker-compose restart api

# Servisleri durdur
docker-compose down
```

## Manuel Başlatma (Docker olmadan)

```bash
cd /Users/enes/AgentWorkspace/Backtest

# Terminal 1: Backend
source .venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (geliştirme)
cd piyasapilot-v2
npx vite --port 5173

# Terminal 3: Frontend (üretim build)
cd piyasapilot-v2
npx vite build
# index.html ana dizine kopyala, FastAPI root'tan servis eder
```

## Healthcheck

Tüm servislerin sağlığını doğrula:

```bash
# Gateway
curl -sf http://localhost:8000/api/health && echo "✅ Gateway OK" || echo "❌ Gateway DOWN"

# Cache yeterliliği
curl -sf http://localhost:8000/api/health | python3 -c "
import sys, json
h = json.load(sys.stdin)
rows = h['cache']['rows']
print(f'{'✅' if rows > 100 else '⚠️'} Cache: {rows} bar')
"
```

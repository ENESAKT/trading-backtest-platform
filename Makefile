.PHONY: up down restart logs status build dev test lint

# ─── Docker Compose ────────────────────────────────────────────────────────

up: build
	docker-compose up -d
	@echo "✅ PiyasaPilot servisleri başlatıldı"
	@docker-compose ps

down:
	docker-compose down
	@echo "🛑 Servisler durduruldu"

restart:
	docker-compose restart
	@echo "🔄 Servisler yeniden başlatıldı"

logs:
	docker-compose logs --tail 100 -f

status:
	@docker-compose ps
	@echo ""
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo "⚠️  Gateway çalışmıyor"

# ─── Build ─────────────────────────────────────────────────────────────────

build:
	cd piyasapilot-v2 && npx vite build
	docker-compose build

# ─── Development ───────────────────────────────────────────────────────────

dev:
	@echo "🚀 Geliştirme ortamı başlatılıyor..."
	@echo "Terminal 1: Backend (bu terminal)"
	source .venv/bin/activate && uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd piyasapilot-v2 && npx vite --port 5173

# ─── Test ──────────────────────────────────────────────────────────────────

test:
	source .venv/bin/activate && python -m pytest tests/ -x -q --timeout=30 -k "not test_ws_quotes_symbol_filter"

test-full:
	source .venv/bin/activate && python -m pytest tests/ -v --timeout=30

lint:
	cd piyasapilot-v2 && npx tsc --noEmit
	cd piyasapilot-v2 && npx vite build

# ─── Utility ───────────────────────────────────────────────────────────────

health:
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool

paper:
	@curl -sf http://localhost:8000/api/paper/wallets | python3 -m json.tool

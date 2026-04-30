.PHONY: up down restart logs status build dev test lint e2e mcp-check stress-smoke stress-live docker-restart-check verify monitor daily-report wal-check

# ─── Docker Compose ────────────────────────────────────────────────────────

up: build
	docker compose up -d
	@echo "✅ PiyasaPilot servisleri başlatıldı"
	@docker compose ps

down:
	docker compose down
	@echo "🛑 Servisler durduruldu"

restart:
	docker compose restart
	@echo "🔄 Servisler yeniden başlatıldı"

logs:
	docker compose logs --tail 100 -f

status:
	@docker compose ps
	@echo ""
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo "⚠️  Gateway çalışmıyor"

# ─── Build ─────────────────────────────────────────────────────────────────

build:
	cd piyasapilot-v2 && npx vite build
	docker compose build

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

e2e:
	cd piyasapilot-v2 && npm run e2e

mcp-check:
	source .venv/bin/activate && python scripts/verify_mcp.py
	claude mcp list

stress-smoke:
	source .venv/bin/activate && python scripts/stress_live_data.py --duration-seconds 30 --symbols 30 --concurrency 10 --max-fail-rate 0.05

stress-live:
	source .venv/bin/activate && python scripts/stress_live_data.py --duration-seconds 3600 --symbols 100 --concurrency 20 --max-fail-rate 0.02

docker-restart-check:
	bash scripts/docker_restart_check.sh

verify: test lint e2e mcp-check

# ─── Utility ───────────────────────────────────────────────────────────────

health:
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool

paper:
	@curl -sf http://localhost:8000/api/paper/wallets | python3 -m json.tool

# ─── Monitoring (Grafana + Prometheus) ─────────────────────────────────

monitor:
	docker compose -f docker-compose.yml -f docker-compose.monitor.yml up -d
	@echo "📊 Grafana: http://localhost:3000 (admin/piyasapilot)"
	@echo "📈 Prometheus: http://localhost:9090"
	@echo "📉 Metrics: http://localhost:8000/metrics"

monitor-down:
	docker compose -f docker-compose.yml -f docker-compose.monitor.yml down

daily-report:
	source .venv/bin/activate && python scripts/daily_health_report.py

daily-report-stdout:
	source .venv/bin/activate && python scripts/daily_health_report.py --no-telegram

wal-check:
	source .venv/bin/activate && python scripts/wal_checkpoint_test.py


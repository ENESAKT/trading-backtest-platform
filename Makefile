.PHONY: up run down clean-containers restart logs status build dev test lint e2e mcp-check stress-smoke stress-live docker-restart-check provider-check provider-check-strict provider-mock-check metrics-check retrain verify monitor daily-report wal-check data-inventory data-size-report health-check backup-now env-production tls-setup install-backup-cron borfin-ocr-inventory skill-source-check

# ─── Docker Compose ────────────────────────────────────────────────────────

COMPOSE = docker compose -f infra/docker-compose.yml
PIYASAPILOT_CONTAINERS = piyasapilot-api piyasapilot-notifier piyasapilot-nginx
PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

up: build
	$(MAKE) clean-containers
	$(COMPOSE) up -d
	@echo "✅ PiyasaPilot servisleri başlatıldı"
	@$(COMPOSE) ps

run: up

down:
	$(COMPOSE) down --remove-orphans
	$(MAKE) clean-containers
	@echo "🛑 Servisler durduruldu"

clean-containers:
	@docker rm -f $(PIYASAPILOT_CONTAINERS) >/dev/null 2>&1 || true

restart:
	$(COMPOSE) restart
	@echo "🔄 Servisler yeniden başlatıldı"

logs:
	$(COMPOSE) logs --tail 100 -f

status:
	@$(COMPOSE) ps
	@echo ""
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo "⚠️  Gateway çalışmıyor"

# ─── Build ─────────────────────────────────────────────────────────────────

build:
	cd frontend && npx vite build
	$(COMPOSE) build

# ─── Development ───────────────────────────────────────────────────────────

dev:
	@echo "🚀 Geliştirme ortamı başlatılıyor..."
	@echo "Terminal 1: Backend (bu terminal)"
	source .venv/bin/activate && uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npx vite --port 5173

# ─── Test ──────────────────────────────────────────────────────────────────

test:
	source .venv/bin/activate && python -m pytest tests/ -x -q --timeout=30 -k "not test_ws_quotes_symbol_filter"

test-full:
	source .venv/bin/activate && python -m pytest tests/ -v --timeout=30

lint:
	cd frontend && npx tsc --noEmit
	cd frontend && npx vite build

e2e:
	cd frontend && npm run e2e

mcp-check:
	source .venv/bin/activate && python scripts/verify_mcp.py
	claude mcp list

stress-smoke:
	source .venv/bin/activate && python scripts/stress_live_data.py --duration-seconds 30 --symbols 30 --concurrency 10 --max-fail-rate 0.05

stress-live:
	source .venv/bin/activate && python scripts/stress_live_data.py --duration-seconds 3600 --symbols 100 --concurrency 20 --max-fail-rate 0.02

docker-restart-check:
	bash scripts/docker_restart_check.sh

provider-check:
	source .venv/bin/activate && python scripts/provider_feed_check.py

provider-check-strict:
	source .venv/bin/activate && python scripts/provider_feed_check.py --require-config

provider-mock-check:
	source .venv/bin/activate && python scripts/provider_feed_check.py --mock --require-config

metrics-check:
	source .venv/bin/activate && python scripts/metrics_live_check.py

retrain:
	source .venv/bin/activate && python scripts/retrain_lightgbm.py --symbol BTCUSDT --interval 15m --output models/lightgbm/BTCUSDT_15m.txt

verify: test lint e2e mcp-check provider-check provider-mock-check

# ─── Data Platform ───────────────────────────────────────────────────────────

data-inventory:
	$(PYTHON) scripts/data_platform/inventory_sync.py

data-size-report:
	@echo "=== ClickHouse Tablo Boyutları ==="
	@curl -s "$$CLICKHOUSE_URL" --data \
		"SELECT table, formatReadableSize(sum(bytes)) AS size, sum(rows) AS rows \
		 FROM system.parts WHERE active GROUP BY table ORDER BY sum(bytes) DESC" \
		2>/dev/null || echo "[!] ClickHouse bağlantısı kurulamadı — CLICKHOUSE_URL env var kontrol et"
	@echo ""
	@echo "=== MySQL Tablo Boyutları ==="
	@mysql -h $${MYSQL_HOST:-localhost} -u $${MYSQL_USER:-appuser} -p$${MYSQL_PASSWORD} \
		$${MYSQL_DATABASE:-piyasapilot} -e \
		"SELECT table_name, ROUND(data_length/1024/1024,2) AS 'MB', table_rows \
		 FROM information_schema.tables WHERE table_schema=DATABASE() ORDER BY data_length DESC;" \
		2>/dev/null || echo "[!] MySQL bağlantısı kurulamadı"

health-check:
	$(PYTHON) scripts/data_platform/health_check.py

prod-health:
	$(PYTHON) scripts/data_platform/health_check.py --prod

derive-timeframes:
	python3 -m backend.data.ingest.derive_timeframes

retention-cleanup:
	python3 -m backend.data.ingest.retention

backfill-bist100:
	python3 -m backend.data.ingest.backfill --market BIST --target 100

backfill-viop:
	python3 -m backend.data.ingest.backfill --market VIOP

# ─── Deployment & Cleanup ─────────────────────────────────────────────────

repo-cleanup-report:
	$(PYTHON) scripts/deployment/repo_cleanup_report.py

borfin-integration-check:
	$(PYTHON) scripts/deployment/borfin_check.py

borfin-ocr-inventory:
	$(PYTHON) scripts/deployment/borfin_ocr_inventory.py

production-package-check:
	$(PYTHON) scripts/deployment/production_package_check.py

docker-context-size:
	du -sh . --exclude=.git --exclude=.venv --exclude=artifacts

deployment-check:
	$(PYTHON) scripts/deployment/deployment_check.py

skill-source-check:
	$(PYTHON) scripts/deployment/skill_source_check.py

backup-now:
	bash scripts/deployment/backup_now.sh

env-production:
	$(PYTHON) scripts/deployment/create_env_production.py

tls-setup:
	bash scripts/deployment/setup_tls.sh

install-backup-cron:
	bash scripts/deployment/install_backup_cron.sh

# ─── Utility ───────────────────────────────────────────────────────────────

health:
	@curl -sf http://localhost:8000/api/health | python3 -m json.tool

paper:
	@curl -sf http://localhost:8000/api/paper/wallets | python3 -m json.tool

# ─── Monitoring (Grafana + Prometheus) ─────────────────────────────────

monitor:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.monitor.yml up -d
	@echo "📊 Grafana: http://localhost:3000 (admin/piyasapilot)"
	@echo "📈 Prometheus: http://localhost:9090"
	@echo "📉 Metrics: http://localhost:8000/metrics"

monitor-down:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.monitor.yml down

daily-report:
	source .venv/bin/activate && python scripts/daily_health_report.py

daily-report-stdout:
	source .venv/bin/activate && python scripts/daily_health_report.py --no-telegram

wal-check:
	source .venv/bin/activate && python scripts/wal_checkpoint_test.py

# PiyasaPilot / Trading Backtest Platform

Local-first engineering project for experimenting with market-data ingestion, screening, paper trading and reproducible backtests. It combines a FastAPI backend, a typed web client, a Flutter client and containerized data services.

> Educational software only. It is not financial advice, a brokerage service or a promise of investment performance.

## Verified scope

- Backend unit suite and mock-based integration tests run in GitHub Actions.
- The web client is type-checked and built with Vite.
- The Flutter client is analyzed and tested.
- API and frontend container images are built in CI; the API image is scanned with Trivy.
- Secrets are supplied through environment variables and are not committed.

There is currently **no supported public deployment**. The former project domain is not presented as a live demo; use the local setup below.

## Local setup

Requirements: Docker with Compose, Git and enough memory for MySQL, Redis and ClickHouse.

```bash
cp .env.production.example .env.production
```

Replace every `BURAYA_YAZ` value. Generate unique local values instead of reusing production credentials:

```bash
openssl rand -hex 64  # JWT_SECRET
openssl rand -hex 32  # API_KEY and database passwords
```

Validate and start the local stack:

```bash
docker compose --env-file .env.production -f infra/docker-compose.local.yml config
docker compose --env-file .env.production -f infra/docker-compose.local.yml up --build
```

- Web: `http://localhost`
- API health: `http://localhost/api/health`

Stop the stack with:

```bash
docker compose --env-file .env.production -f infra/docker-compose.local.yml down
```

## Checks without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/unit/ -q --ignore=tests/unit/test_binance_ws.py --ignore=tests/unit/test_live_feed.py

cd frontend
npm ci
npm run build

cd ../mobile/piyasapilot_mobile
flutter pub get
flutter analyze --no-fatal-infos --no-fatal-warnings
flutter test
```

## Repository map

- `backend/`: API, authentication, data access and operational endpoints
- `quant_engine/`: indicators, backtesting and paper-trading logic
- `frontend/`: TypeScript web client
- `mobile/piyasapilot_mobile/`: Flutter client
- `infra/` and `docker/`: local/production container definitions
- `tests/`: unit and mock-based integration coverage
- `docs/SECURITY.md`: security model and operational guidance

## Limitations

- Live exchange and provider tests are excluded from the deterministic CI suite.
- Real deployments require separately managed infrastructure, DNS, TLS and third-party credentials.
- Backtest results depend on data quality, assumptions, fees and slippage; they must not be interpreted as future returns.

# Deployment

## Purpose

Deployment katmanı Docker Compose, nginx, build ve servis sağlık akışlarını tutar.

## Source Files

- `Makefile`
- `infra/docker-compose.yml`
- `infra/docker/`
- `infra/nginx/`
- `docker/`
- `docs/DEPLOYMENT.md`

## Current Facts

- `make up` frontend build, compose build ve compose up akışını çalıştırır.
- `make run` `make up` alias'ıdır.
- Compose servisleri `piyasapilot-api`, `piyasapilot-notifier`, `piyasapilot-nginx`
  container adlarını kullanır.
- İsim çakışmalarını önlemek için Makefile `clean-containers` hedefini kullanır.
- Nginx statik frontend çıktısını `frontend/dist` üzerinden servis eder.

## Related

- [[../01-maps/backend-map]]
- [[../01-maps/frontend-map]]


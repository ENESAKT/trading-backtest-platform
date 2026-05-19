#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-piyasapilotu.com}"
EMAIL="${EMAIL:-admin@piyasapilotu.com}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env.production ]; then
  echo "HATA: .env.production bulunamadi. Once sunucuda gercek production env dosyasini olustur."
  exit 1
fi

if grep -q "BURAYA_YAZ" .env.production; then
  echo "HATA: .env.production icinde BURAYA_YAZ placeholder degerleri kalmis."
  exit 1
fi

mkdir -p infra/certbot/conf infra/certbot/www

if [ -f "infra/certbot/conf/live/${DOMAIN}/fullchain.pem" ] && [ "${FORCE_TLS:-0}" != "1" ]; then
  echo "TLS sertifikasi zaten var: ${DOMAIN}"
  exit 0
fi

echo "HTTP bootstrap nginx baslatiliyor..."
NGINX_CONF=../docker/nginx.bootstrap.conf \
  docker compose --env-file .env.production -f infra/docker-compose.prod.yml up -d --build nginx

echo "Let's Encrypt sertifikasi aliniyor: ${DOMAIN}, www.${DOMAIN}"
docker run --rm \
  -v "$ROOT_DIR/infra/certbot/conf:/etc/letsencrypt" \
  -v "$ROOT_DIR/infra/certbot/www:/var/www/certbot" \
  certbot/certbot:latest certonly \
    --webroot \
    -w /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.${DOMAIN}"

echo "Production TLS nginx aktif ediliyor..."
docker compose --env-file .env.production -f infra/docker-compose.prod.yml up -d nginx

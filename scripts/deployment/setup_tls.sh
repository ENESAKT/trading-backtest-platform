#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-admin@example.com}"
CERTBOT_CONF_DIR="${CERTBOT_CONF_DIR:-$ROOT_DIR/infra/certbot/conf}"
CERTBOT_WORK_DIR="${CERTBOT_WORK_DIR:-$ROOT_DIR/infra/certbot/work}"
CERTBOT_LOG_DIR="${CERTBOT_LOG_DIR:-$ROOT_DIR/infra/certbot/logs}"
WEBROOT="${WEBROOT:-$ROOT_DIR/infra/certbot/www}"

if [[ -z "$DOMAIN" ]]; then
  echo "DOMAIN zorunlu. Örnek: DOMAIN=piyasapilot.example.com EMAIL=admin@example.com $0" >&2
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y certbot python3-certbot-nginx
fi

mkdir -p "$CERTBOT_CONF_DIR" "$CERTBOT_WORK_DIR" "$CERTBOT_LOG_DIR" "$WEBROOT"
sudo certbot certonly --webroot \
  --config-dir "$CERTBOT_CONF_DIR" \
  --work-dir "$CERTBOT_WORK_DIR" \
  --logs-dir "$CERTBOT_LOG_DIR" \
  -w "$WEBROOT" \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive

echo "TLS sertifikası hazır: $CERTBOT_CONF_DIR/live/$DOMAIN"

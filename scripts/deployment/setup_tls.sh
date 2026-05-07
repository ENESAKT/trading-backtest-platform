#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-admin@example.com}"
WEBROOT="${WEBROOT:-/var/www/certbot}"

if [[ -z "$DOMAIN" ]]; then
  echo "DOMAIN zorunlu. Örnek: DOMAIN=piyasapilot.example.com EMAIL=admin@example.com $0" >&2
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y certbot python3-certbot-nginx
fi

sudo mkdir -p "$WEBROOT"
sudo certbot certonly --webroot \
  -w "$WEBROOT" \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive

echo "TLS sertifikası hazır: /etc/letsencrypt/live/$DOMAIN"

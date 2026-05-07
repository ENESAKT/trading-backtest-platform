#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/infra/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Eksik env dosyası: $ENV_FILE" >&2
  exit 1
fi

MYSQL_BACKUP_NAME="mysql_piyasapilot_${STAMP}.sql.gz"
CLICKHOUSE_BACKUP_NAME="clickhouse_piyasapilot_${STAMP}"

echo "MySQL dump alınıyor..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mysql \
  sh -c 'mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' \
  | gzip -9 > "$BACKUP_DIR/$MYSQL_BACKUP_NAME"

echo "ClickHouse native backup başlatılıyor..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T \
  -e CH_BACKUP_NAME="$CLICKHOUSE_BACKUP_NAME" \
  clickhouse sh -c \
  'clickhouse-client --user "${CLICKHOUSE_USER:-default}" --password "${CLICKHOUSE_PASSWORD:-}" --query "BACKUP DATABASE ${CLICKHOUSE_DB:-piyasapilot} TO Disk('\''backups'\'', '\''${CH_BACKUP_NAME}'\'')"'

echo "Backup tamamlandı: $BACKUP_DIR"

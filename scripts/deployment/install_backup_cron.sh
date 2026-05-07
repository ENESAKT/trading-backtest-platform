#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCHEDULE="${SCHEDULE:-17 2 * * *}"
CRON_LINE="$SCHEDULE cd $ROOT_DIR && /usr/bin/env bash scripts/deployment/backup_now.sh >> logs/backup.log 2>&1"

mkdir -p "$ROOT_DIR/logs"
(crontab -l 2>/dev/null | grep -v "scripts/deployment/backup_now.sh" || true; echo "$CRON_LINE") | crontab -
echo "Backup cron kuruldu: $CRON_LINE"

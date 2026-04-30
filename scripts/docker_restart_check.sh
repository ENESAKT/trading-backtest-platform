#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

wait_health() {
  local deadline=$((SECONDS + 45))
  until curl -sf "$BASE_URL/api/health" >/dev/null; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "api healthcheck 45 sn içinde dönmedi" >&2
      docker compose ps >&2
      exit 1
    fi
    sleep 2
  done
}

docker compose ps >/dev/null
docker compose up -d api >/dev/null
wait_health
api_container="$(docker compose ps -q api)"
if [ -z "$api_container" ]; then
  echo "api container bulunamadı" >&2
  exit 1
fi
started_at="$(docker inspect --format '{{.State.StartedAt}}' "$api_container")"

docker compose restart api >/dev/null
deadline=$((SECONDS + 45))
while [ "$(docker inspect --format '{{.State.StartedAt}}' "$api_container" 2>/dev/null || true)" = "$started_at" ]; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "api container yeniden başlamadı" >&2
    docker compose ps >&2
    exit 1
  fi
  sleep 1
done
wait_health

echo "✅ api restart sonrası sağlıklı"

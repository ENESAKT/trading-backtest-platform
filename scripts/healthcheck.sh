#!/usr/bin/env bash
set -euo pipefail

echo "Running healthcheck..."
DEGRADED=0

# 1. HTTP API Check
echo "Checking HTTP API health..."
HTTP_RESPONSE=$(curl -sf http://localhost:8000/api/health || echo "FAIL")
if [[ "$HTTP_RESPONSE" == "FAIL" ]]; then
  echo "API health check failed. Could not reach /api/health."
  DEGRADED=1
elif ! echo "$HTTP_RESPONSE" | grep -q '"status":"ok"'; then
  echo "API health check failed. Response: $HTTP_RESPONSE"
  DEGRADED=1
else
  echo "API is healthy."
fi

# 2. Docker Containers Check
echo "Checking Docker containers..."
if command -v docker >/dev/null 2>&1; then
  NOT_RUNNING=$(docker ps -a --format "{{.Names}} {{.Status}}" | grep -v "Up " || true)
  if [[ -n "$NOT_RUNNING" ]]; then
    echo "Warning: Some containers are not running!"
    echo "$NOT_RUNNING"
    DEGRADED=1
  else
    echo "All Docker containers are Up."
  fi
else
  echo "Docker command not found, skipping container check."
fi

# 3. Disk Space Check
echo "Checking disk usage..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
  echo "Warning: Disk usage is over 80% ($DISK_USAGE%)."
  DEGRADED=1
else
  echo "Disk usage is normal ($DISK_USAGE%)."
fi

# 4. Memory Check
echo "Checking memory usage..."
AVAILABLE_MEM=$(free -m | awk 'NR==2 {print $7}')
if [ "$AVAILABLE_MEM" -lt 200 ]; then
  echo "Warning: Available memory is very low (${AVAILABLE_MEM}MB)."
  DEGRADED=1
else
  echo "Available memory is normal (${AVAILABLE_MEM}MB)."
fi

if [ "$DEGRADED" -eq 1 ]; then
  echo "Healthcheck DEGRADED."
  exit 1
else
  echo "Healthcheck PASSED. System is healthy."
  exit 0
fi

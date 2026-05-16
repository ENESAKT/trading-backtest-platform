#!/usr/bin/env bash
set -euo pipefail

RESTORE_DIR="/tmp/restore_test"
S3_BUCKET="s3://piyasapilot-backups/daily/"

echo "Starting restore test drill..."

# Clean previous restore attempts
rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"

# Get latest backup file from S3
LATEST_BACKUP=$(aws s3 ls "$S3_BUCKET" | sort | tail -n 1 | awk '{print $4}')

if [ -z "$LATEST_BACKUP" ]; then
  echo "FAIL: No backups found in S3."
  exit 1
fi

echo "Downloading latest backup: $LATEST_BACKUP"
aws s3 cp "${S3_BUCKET}${LATEST_BACKUP}" "${RESTORE_DIR}/latest_backup.tar.gz"

echo "Extracting backup..."
cd "$RESTORE_DIR"
tar -xzf latest_backup.tar.gz

# Check integrity of all extracted sqlite databases
FAIL_COUNT=0
PASS_COUNT=0

for db in $(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3"); do
  echo "Checking integrity of $db..."
  RESULT=$(sqlite3 "$db" "PRAGMA integrity_check;")
  
  if [ "$RESULT" == "ok" ]; then
    echo "PASS: $db integrity is ok."
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL: $db integrity check failed! Result: $RESULT"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "Restore test FAILED. $FAIL_COUNT databases failed integrity check."
  exit 1
else
  echo "Restore test PASSED. $PASS_COUNT databases passed integrity check."
  exit 0
fi

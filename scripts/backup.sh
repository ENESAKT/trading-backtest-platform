#!/usr/bin/env bash
set -euo pipefail

# Constants
BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DIR="/tmp"
BACKUP_FILE="${BACKUP_DIR}/backup_${BACKUP_DATE}.tar.gz"
S3_BUCKET="s3://piyasapilot-backups/daily/"
DATA_DIR="/opt/piyasapilot/data"

echo "Starting backup process for $BACKUP_DATE"

# Ensure data directory exists before proceeding
if [ ! -d "$DATA_DIR" ]; then
  echo "Data directory $DATA_DIR does not exist. Nothing to backup."
  exit 0
fi

# Find all sqlite databases and archive them
find "$DATA_DIR" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" > /tmp/db_list.txt
if [ -s /tmp/db_list.txt ]; then
  tar -czf "$BACKUP_FILE" -T /tmp/db_list.txt
  echo "Created archive: $BACKUP_FILE"
  
  # Upload to S3
  echo "Uploading to S3..."
  aws s3 cp "$BACKUP_FILE" "$S3_BUCKET"
  
  echo "Backup successfully uploaded to $S3_BUCKET"
else
  echo "No sqlite databases found in $DATA_DIR"
fi

# Cleanup old backups (older than 3 days)
echo "Cleaning up backups older than 3 days..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +3 -exec rm {} \;

echo "Backup process completed."

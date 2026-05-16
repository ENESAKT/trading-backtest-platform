#!/usr/bin/env bash
set -euo pipefail

BUCKET="${BACKUP_BUCKET:-piyasapilot-backups-prod}"
WORKDIR="${RESTORE_DRILL_DIR:-/tmp/piyasapilot_restore_drill}"

rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

BACKUP="$(aws s3 ls "s3://${BUCKET}/" | sort | tail -1 | awk '{print $4}')"
if [[ -z "${BACKUP}" ]]; then
  echo "No backup found in s3://${BUCKET}/" >&2
  exit 1
fi

aws s3 cp "s3://${BUCKET}/${BACKUP}" "${WORKDIR}/backup.tar.gz.gpg"
gpg --batch --yes --decrypt --passphrase "${BACKUP_GPG_PASSPHRASE:?BACKUP_GPG_PASSPHRASE required}" \
  "${WORKDIR}/backup.tar.gz.gpg" | tar -xzf - -C "$WORKDIR"

echo "Restore drill extracted ${BACKUP} into ${WORKDIR}"

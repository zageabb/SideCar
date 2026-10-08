#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup-file.tar.gz>" >&2
  exit 2
fi

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BACKUP_FILE="$1"
VOLUME_NAME="${SIDECAR_VOLUME_NAME:-sidecar_sidecar-data}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup not found: $BACKUP_FILE" >&2
  exit 2
fi

BACKUP_DIR="$(CDPATH= cd -- "$(dirname -- "$BACKUP_FILE")" && pwd)"
BACKUP_NAME="$(basename -- "$BACKUP_FILE")"

docker compose -f "$PROJECT_ROOT/docker-compose.yml" stop sidecar
trap 'docker compose -f "$PROJECT_ROOT/docker-compose.yml" start sidecar >/dev/null 2>&1 || true' EXIT

docker run --rm \
  -v "$VOLUME_NAME:/target" \
  -v "$BACKUP_DIR:/backup:ro" \
  alpine sh -c "rm -rf /target/* && tar xzf /backup/$BACKUP_NAME -C /target"

docker compose -f "$PROJECT_ROOT/docker-compose.yml" start sidecar
trap - EXIT

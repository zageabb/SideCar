#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BACKUP_DIR="${SIDECAR_BACKUP_DIR:-$PROJECT_ROOT/backups}"
VOLUME_NAME="${SIDECAR_VOLUME_NAME:-sidecar_sidecar-data}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="sidecar-data-$STAMP.tar.gz"

docker compose -f "$PROJECT_ROOT/docker-compose.yml" stop sidecar
trap 'docker compose -f "$PROJECT_ROOT/docker-compose.yml" start sidecar >/dev/null 2>&1 || true' EXIT

docker run --rm \
  -v "$VOLUME_NAME:/source:ro" \
  -v "$BACKUP_DIR:/backup" \
  alpine sh -c "cd /source && tar czf /backup/$FILE ."

docker compose -f "$PROJECT_ROOT/docker-compose.yml" start sidecar
trap - EXIT

printf '%s\n' "$BACKUP_DIR/$FILE"

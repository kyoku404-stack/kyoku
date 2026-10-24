#!/usr/bin/env bash
# ==============================================================================
# KEEP Enterprise Platform — Production Automated Disaster Recovery Backup
# ==============================================================================
# Specification: devdocs/p1/p1.10.txt (Chapters 12, 13, 18) & ADR-031
# Architecture: docs/Architecture/deployment-ai-infrastructure.md
# Role: Member 4 (DevOps & Integration Lead)
# ==============================================================================

set -euo pipefail

# ANSI Styling
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

BACKUP_ROOT="${BACKUP_DIR:-./backups/production}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SNAPSHOT_DIR="${BACKUP_ROOT}/snapshot_${TIMESTAMP}"
COMPOSE_FILE="docker-compose.prod.yml"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

log_info() { echo -e "${CYAN}[INFO]${RESET} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
log_error() { echo -e "${RED}[ERROR]${RESET} $1"; }

mkdir -p "$SNAPSHOT_DIR"

log_info "Starting production backup snapshot: ${SNAPSHOT_DIR}"

# 1. PostgreSQL Database Dump (Custom Compressed Binary Format)
log_info "Exporting PostgreSQL database dump..."
DB_FILE="${SNAPSHOT_DIR}/postgres_database.dump"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
    -U "${POSTGRES_USER:-keep_user}" \
    -d "${POSTGRES_DB:-keep_db}" \
    --format=custom \
    --blobs > "$DB_FILE"
log_success "PostgreSQL dump completed: $(du -h "$DB_FILE" | cut -f1)"

# 2. Multi-Tenant Storage Filesystem Archive
log_info "Archiving persistent multi-tenant document storage..."
STORAGE_FILE="${SNAPSHOT_DIR}/storage_volume.tar.gz"
if docker compose -f "$COMPOSE_FILE" ps backend | grep -q "Up"; then
    docker compose -f "$COMPOSE_FILE" exec -T backend tar -czf - -C /app/storage . > "$STORAGE_FILE"
elif [[ -d "./storage" ]]; then
    tar -czf "$STORAGE_FILE" -C ./storage .
else
    tar -czf "$STORAGE_FILE" --files-from /dev/null
fi
log_success "Storage filesystem archived: $(du -h "$STORAGE_FILE" | cut -f1)"

# 3. Cryptographic SHA-256 Manifest Generation
log_info "Generating cryptographic SHA-256 manifest..."
DB_SHA256=$(sha256sum "$DB_FILE" | cut -d' ' -f1)
STORAGE_SHA256=$(sha256sum "$STORAGE_FILE" | cut -d' ' -f1)

cat <<EOF > "${SNAPSHOT_DIR}/manifest.json"
{
  "platform": "KEEP Enterprise Platform",
  "backup_version": "1.0",
  "timestamp": "${TIMESTAMP}",
  "created_at_iso": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "slo_target": "RPO < 1 hour, RTO < 15 minutes",
  "artifacts": [
    {
      "name": "postgres_database.dump",
      "type": "database",
      "format": "pg_dump_custom",
      "size_bytes": $(wc -c < "$DB_FILE"),
      "sha256": "${DB_SHA256}"
    },
    {
      "name": "storage_volume.tar.gz",
      "type": "storage_filesystem",
      "format": "tar_gzip",
      "size_bytes": $(wc -c < "$STORAGE_FILE"),
      "sha256": "${STORAGE_SHA256}"
    }
  ]
}
EOF
log_success "Manifest generated at ${SNAPSHOT_DIR}/manifest.json"

# 4. Backup Retention Pruning
log_info "Pruning production backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -name "snapshot_*" -mtime +"$RETENTION_DAYS" -exec rm -rf {} + || true

log_success "Production backup complete: ${SNAPSHOT_DIR}"

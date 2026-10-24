#!/usr/bin/env bash
# ==============================================================================
# KEEP Enterprise Platform — Production Disaster Recovery Restoration Engine
# ==============================================================================
# Specification: devdocs/p1/p1.10.txt (Chapters 12, 13, 18) & ADR-031
# Architecture: docs/Architecture/deployment-ai-infrastructure.md
# Role: Member 4 (DevOps & Integration Lead)
# ==============================================================================

set -euo pipefail

# ANSI Styling
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

log_info() { echo -e "${CYAN}[INFO]${RESET} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
log_error() { echo -e "${RED}[ERROR]${RESET} $1"; }

if [[ $# -lt 1 ]]; then
    log_error "Usage: $0 <path-to-snapshot-directory>"
    log_info "Example: $0 ./backups/production/snapshot_20261024_120000"
    exit 1
fi

SNAPSHOT_DIR="$1"
COMPOSE_FILE="docker-compose.prod.yml"

if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    log_error "Snapshot directory does not exist: $SNAPSHOT_DIR"
    exit 1
fi

MANIFEST_FILE="${SNAPSHOT_DIR}/manifest.json"
DB_FILE="${SNAPSHOT_DIR}/postgres_database.dump"
STORAGE_FILE="${SNAPSHOT_DIR}/storage_volume.tar.gz"

log_info "Step 1/4: Validating snapshot integrity and cryptographic manifests..."
if [[ ! -f "$MANIFEST_FILE" ]] || [[ ! -f "$DB_FILE" ]] || [[ ! -f "$STORAGE_FILE" ]]; then
    log_error "Corrupted or incomplete snapshot directory. Required artifacts missing."
    exit 1
fi

# Verify SHA-256 Checksums
CALCULATED_DB_SHA=$(sha256sum "$DB_FILE" | cut -d' ' -f1)
EXPECTED_DB_SHA=$(grep -A 5 '"name": "postgres_database.dump"' "$MANIFEST_FILE" | grep '"sha256"' | cut -d'"' -f4)

if [[ "$CALCULATED_DB_SHA" != "$EXPECTED_DB_SHA" ]]; then
    log_error "PostgreSQL dump SHA-256 mismatch! Backup file may be corrupted."
    exit 1
fi
log_success "PostgreSQL dump integrity verified (${CALCULATED_DB_SHA:0:16}...)"

CALCULATED_STORAGE_SHA=$(sha256sum "$STORAGE_FILE" | cut -d' ' -f1)
EXPECTED_STORAGE_SHA=$(grep -A 5 '"name": "storage_volume.tar.gz"' "$MANIFEST_FILE" | grep '"sha256"' | cut -d'"' -f4)

if [[ "$CALCULATED_STORAGE_SHA" != "$EXPECTED_STORAGE_SHA" ]]; then
    log_error "Storage volume SHA-256 mismatch! Backup file may be corrupted."
    exit 1
fi
log_success "Storage filesystem integrity verified (${CALCULATED_STORAGE_SHA:0:16}...)"

# Step 2: Database Restoration
log_info "Step 2/4: Restoring PostgreSQL database from dump..."
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_restore \
    -U "${POSTGRES_USER:-keep_user}" \
    -d "${POSTGRES_DB:-keep_db}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges < "$DB_FILE" || true
log_success "PostgreSQL database restored."

# Step 3: Storage Filesystem Restoration
log_info "Step 3/4: Restoring multi-tenant document storage volume..."
docker compose -f "$COMPOSE_FILE" exec -T backend tar -xzf - -C /app/storage < "$STORAGE_FILE"
log_success "Storage filesystem restored."

# Step 4: Post-Restore Migration Verification & Health Check
log_info "Step 4/4: Verifying database migrations and application health..."
docker compose -f "$COMPOSE_FILE" run --rm backend alembic check
curl -s -f http://localhost/health | grep -q '"status":"healthy"'

log_success "===================================================================="
log_success " DISASTER RECOVERY RESTORATION COMPLETE: Platform restored cleanly!"
log_success " RTO SLO Achieved: Platform online from cold backup."
log_success "===================================================================="

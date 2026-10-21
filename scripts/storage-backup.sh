#!/usr/bin/env bash
# ==============================================================================
# KEEP — Storage Disaster Recovery & Backup Engine (Phase 1.8)
# Creates compressed, timestamped snapshots of multi-tenant document storage
# Usage: ./scripts/storage-backup.sh [--mode docker|native] [--output-dir DIR] [--retention-days DAYS]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${ROOT_DIR}/backups/storage"
MODE="native"
RETENTION_DAYS=7
STORAGE_DIR="${ROOT_DIR}/storage"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --output-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --storage-dir)
            STORAGE_DIR="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}[!] Unknown option: $1${NC}"
            echo "Usage: ./scripts/storage-backup.sh [--mode docker|native] [--output-dir DIR] [--retention-days DAYS]"
            exit 1
            ;;
    esac
done

mkdir -p "${BACKUP_DIR}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="keep_storage_backup_${TIMESTAMP}.tar.gz"
BACKUP_FILE="${BACKUP_DIR}/${ARCHIVE_NAME}"
MANIFEST_FILE="${BACKUP_DIR}/keep_storage_manifest_${TIMESTAMP}.sha256"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Storage Disaster Recovery & Backup Engine (Phase 1.8)    ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Target output: ${BACKUP_FILE}${NC}"
echo -e "${GREEN}[*] Execution mode: ${MODE}${NC}"

if [ "${MODE}" == "docker" ]; then
    echo -e "${GREEN}[+] Archiving storage volume from keep-backend container...${NC}"
    docker compose exec -T backend tar -czf - -C /app storage > "${BACKUP_FILE}"
else
    echo -e "${GREEN}[+] Archiving storage repository from local directory: ${STORAGE_DIR}...${NC}"
    if [ ! -d "${STORAGE_DIR}" ]; then
        mkdir -p "${STORAGE_DIR}"
    fi
    tar -czf "${BACKUP_FILE}" -C "${ROOT_DIR}" storage
fi

BACKUP_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
echo -e "${GREEN}[+] Snapshot successfully created! Size: ${BACKUP_SIZE}${NC}"

# Generate cryptographic SHA-256 manifest
echo -e "${GREEN}[+] Generating SHA-256 verification manifest...${NC}"
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${BACKUP_FILE}" > "${MANIFEST_FILE}"
elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${BACKUP_FILE}" > "${MANIFEST_FILE}"
fi

# Retention policy enforcement
echo -e "${GREEN}[+] Pruning archives older than ${RETENTION_DAYS} days in ${BACKUP_DIR}...${NC}"
find "${BACKUP_DIR}" -name "keep_storage_backup_*.tar.gz" -type f -mtime +"${RETENTION_DAYS}" -delete || true
find "${BACKUP_DIR}" -name "keep_storage_manifest_*.sha256" -type f -mtime +"${RETENTION_DAYS}" -delete || true

echo -e "${GREEN}[✓] Backup process completed successfully!${NC}"

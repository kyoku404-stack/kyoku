#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Backup Utility (Chapter 18)
# Usage: ./scripts/db-backup.sh [--mode docker|native] [--output-dir DIR] [--retention-days DAYS]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${ROOT_DIR}/backups"
MODE="docker"
RETENTION_DAYS=7

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
        *)
            echo -e "${RED}[!] Unknown option: $1${NC}"
            echo "Usage: ./scripts/db-backup.sh [--mode docker|native] [--output-dir DIR] [--retention-days DAYS]"
            exit 1
            ;;
    esac
done

mkdir -p "${BACKUP_DIR}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/keep_backup_${TIMESTAMP}.sql.gz"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP PostgreSQL Database Backup Engine                        ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Target output: ${BACKUP_FILE}${NC}"
echo -e "${GREEN}[*] Execution mode: ${MODE}${NC}"

DB_USER="${POSTGRES_USER:-keep_user}"
DB_NAME="${POSTGRES_DB:-keep_db}"

if [ "${MODE}" == "docker" ]; then
    echo -e "${GREEN}[+] Exporting database from keep-postgres container...${NC}"
    docker compose exec -T postgres pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"
else
    echo -e "${GREEN}[+] Exporting database via local pg_dump...${NC}"
    DB_HOST="${POSTGRES_SERVER:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    PGPASSWORD="${POSTGRES_PASSWORD:-keep_password}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"
fi

FILE_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
echo -e "${GREEN}[+] Backup created successfully! Size: ${FILE_SIZE}${NC}"

# Retention cleanup
echo -e "${CYAN}[*] Applying retention policy (${RETENTION_DAYS} days)...${NC}"
find "${BACKUP_DIR}" -name "keep_backup_*.sql.gz" -type f -mtime +"${RETENTION_DAYS}" -exec rm -f {} \; || true
echo -e "${GREEN}[+] Backup workflow complete.${NC}"

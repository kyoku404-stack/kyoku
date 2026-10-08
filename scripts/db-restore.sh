#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Restore Utility (Chapter 18)
# Usage: ./scripts/db-restore.sh <backup_file.sql[.gz]> [--mode docker|native] [--force]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo -e "${RED}[!] Error: Missing backup file argument.${NC}"
    echo "Usage: ./scripts/db-restore.sh <backup_file.sql[.gz]> [--mode docker|native] [--force]"
    exit 1
fi

BACKUP_FILE="$1"
shift

MODE="docker"
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${RED}[!] Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}[!] Backup file does not exist: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP PostgreSQL Database Restore Engine                       ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${YELLOW}[!] WARNING: This will overwrite existing database records in target database!${NC}"
echo -e "${GREEN}[*] Source file: ${BACKUP_FILE}${NC}"
echo -e "${GREEN}[*] Execution mode: ${MODE}${NC}"

if [ "${FORCE}" != true ]; then
    read -rp "Are you sure you want to proceed with restore? [y/N]: " CONFIRM
    if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[*] Database restore cancelled by user.${NC}"
        exit 0
    fi
fi

DB_USER="${POSTGRES_USER:-keep_user}"
DB_NAME="${POSTGRES_DB:-keep_db}"

echo -e "${GREEN}[+] Restoring database tables and records...${NC}"

if [[ "${BACKUP_FILE}" == *.gz ]]; then
    DECOMPRESS_CMD="gzip -dc"
else
    DECOMPRESS_CMD="cat"
fi

if [ "${MODE}" == "docker" ]; then
    ${DECOMPRESS_CMD} "${BACKUP_FILE}" | docker compose exec -T postgres psql -U "${DB_USER}" -d "${DB_NAME}"
else
    DB_HOST="${POSTGRES_SERVER:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    PGPASSWORD="${POSTGRES_PASSWORD:-keep_password}" ${DECOMPRESS_CMD} "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"
fi

echo -e "${GREEN}[+] Database restored successfully from ${BACKUP_FILE}!${NC}"

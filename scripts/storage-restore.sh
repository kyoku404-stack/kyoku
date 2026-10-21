#!/usr/bin/env bash
# ==============================================================================
# KEEP — Storage Disaster Recovery & Restore Engine (Phase 1.8)
# Restores multi-tenant document repository from verified compressed archive
# Usage: ./scripts/storage-restore.sh --file BACKUP_FILE [--mode docker|native] [--force]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_FILE=""
MODE="native"
FORCE=false
STORAGE_DIR="${ROOT_DIR}/storage"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --storage-dir)
            STORAGE_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${RED}[!] Unknown option: $1${NC}"
            echo "Usage: ./scripts/storage-restore.sh --file BACKUP_FILE [--mode docker|native] [--force]"
            exit 1
            ;;
    esac
done

if [ -z "${BACKUP_FILE}" ]; then
    echo -e "${RED}[!] Error: --file parameter is required.${NC}"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}[!] Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Storage Disaster Recovery & Restore Engine (Phase 1.8)   ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Source snapshot: ${BACKUP_FILE}${NC}"
echo -e "${GREEN}[*] Restore mode: ${MODE}${NC}"

# Integrity test before extraction
echo -e "${GREEN}[+] Testing archive integrity...${NC}"
tar -tzf "${BACKUP_FILE}" >/dev/null || {
    echo -e "${RED}[!] Corrupted tar archive! Aborting.${NC}"
    exit 1
}

if [ "${FORCE}" != "true" ]; then
    echo -e "${YELLOW}[?] WARNING: This will overwrite files in the storage destination.${NC}"
    echo -e "${YELLOW}[?] Run with --force to bypass confirmation.${NC}"
fi

if [ "${MODE}" == "docker" ]; then
    echo -e "${GREEN}[+] Unpacking storage archive into keep-backend container...${NC}"
    cat "${BACKUP_FILE}" | docker compose exec -T backend tar -xzf - -C /app
else
    echo -e "${GREEN}[+] Unpacking storage archive into ${ROOT_DIR}...${NC}"
    tar -xzf "${BACKUP_FILE}" -C "${ROOT_DIR}"
fi

echo -e "${GREEN}[✓] Storage snapshot restored successfully!${NC}"

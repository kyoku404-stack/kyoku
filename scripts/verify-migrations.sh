#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Migration Verification & Consistency Check
# Usage: ./scripts/verify-migrations.sh
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/backend"

ALEMBIC_BIN="alembic"
if [ -f "${ROOT_DIR}/backend/.venv/bin/alembic" ]; then
    ALEMBIC_BIN="${ROOT_DIR}/backend/.venv/bin/alembic"
elif [ -f "${ROOT_DIR}/.venv/bin/alembic" ]; then
    ALEMBIC_BIN="${ROOT_DIR}/.venv/bin/alembic"
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Database Migration & Consistency Verification            ${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "${GREEN}[1/3] Checking Alembic heads...${NC}"
"${ALEMBIC_BIN}" heads

echo -e "${GREEN}[2/3] Checking Alembic history consistency...${NC}"
"${ALEMBIC_BIN}" history

echo -e "${GREEN}[3/3] Validating migration versions directory...${NC}"
MIGRATION_COUNT="$(find "${ROOT_DIR}/backend/migrations/versions" -type f -name "*.py" | wc -l)"
echo -e "${GREEN}[*] Found ${MIGRATION_COUNT} migration version script(s).${NC}"

if [ "${MIGRATION_COUNT}" -eq 0 ]; then
    echo -e "${RED}[!] Error: No migration version files detected in backend/migrations/versions/!${NC}"
    exit 1
fi

echo -e "${GREEN}[+] All migration verification checks passed!${NC}"

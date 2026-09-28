#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Migration Utility
# Usage: ./scripts/db-migrate.sh [upgrade|downgrade|revision] [args...]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/backend"

COMMAND="${1:-upgrade}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Database Migration Manager (Alembic)                     ${NC}"
echo -e "${CYAN}================================================================${NC}"

if [ "${COMMAND}" == "upgrade" ]; then
    TARGET="${2:-head}"
    echo -e "${GREEN}[+] Running Alembic migrations upgrade to ${TARGET}...${NC}"
    alembic upgrade "${TARGET}"
elif [ "${COMMAND}" == "downgrade" ]; then
    TARGET="${2:--1}"
    echo -e "${YELLOW}[!] Rolling back migrations to ${TARGET}...${NC}"
    alembic downgrade "${TARGET}"
elif [ "${COMMAND}" == "revision" ]; then
    MESSAGE="${2:-new_migration}"
    echo -e "${GREEN}[+] Generating new migration revision: ${MESSAGE}...${NC}"
    alembic revision --autogenerate -m "${MESSAGE}"
elif [ "${COMMAND}" == "current" ]; then
    alembic current
elif [ "${COMMAND}" == "history" ]; then
    alembic history --verbose
else
    echo -e "${YELLOW}Usage: ./scripts/db-migrate.sh [upgrade|downgrade|revision|current|history]${NC}"
    exit 1
fi

echo -e "${GREEN}[+] Database operation completed successfully!${NC}"

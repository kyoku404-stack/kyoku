#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Migration Utility
# Usage: ./scripts/db-migrate.sh [upgrade|downgrade|revision|current|history|test|check] [args...]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/backend"

# Detect Alembic executable
ALEMBIC_BIN="alembic"
if [ -f "${ROOT_DIR}/backend/.venv/bin/alembic" ]; then
    ALEMBIC_BIN="${ROOT_DIR}/backend/.venv/bin/alembic"
elif [ -f "${ROOT_DIR}/.venv/bin/alembic" ]; then
    ALEMBIC_BIN="${ROOT_DIR}/.venv/bin/alembic"
fi

COMMAND="${1:-upgrade}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Database Migration Manager (Alembic)                     ${NC}"
echo -e "${CYAN}================================================================${NC}"

if [ "${COMMAND}" == "upgrade" ]; then
    TARGET="${2:-head}"
    echo -e "${GREEN}[+] Running Alembic migrations upgrade to ${TARGET}...${NC}"
    "${ALEMBIC_BIN}" upgrade "${TARGET}"
elif [ "${COMMAND}" == "downgrade" ]; then
    TARGET="${2:--1}"
    echo -e "${YELLOW}[!] Rolling back migrations to ${TARGET}...${NC}"
    "${ALEMBIC_BIN}" downgrade "${TARGET}"
elif [ "${COMMAND}" == "revision" ]; then
    MESSAGE="${2:-new_migration}"
    echo -e "${GREEN}[+] Generating new migration revision: ${MESSAGE}...${NC}"
    "${ALEMBIC_BIN}" revision --autogenerate -m "${MESSAGE}"
elif [ "${COMMAND}" == "current" ]; then
    "${ALEMBIC_BIN}" current
elif [ "${COMMAND}" == "history" ]; then
    "${ALEMBIC_BIN}" history --verbose
elif [ "${COMMAND}" == "check" ]; then
    echo -e "${GREEN}[+] Checking migration status against heads...${NC}"
    "${ALEMBIC_BIN}" heads
elif [ "${COMMAND}" == "test" ]; then
    echo -e "${GREEN}[+] Testing migration upgrade/downgrade cycle...${NC}"
    echo -e "${CYAN}[1/3] Upgrading to head...${NC}"
    "${ALEMBIC_BIN}" upgrade head
    echo -e "${CYAN}[2/3] Downgrading to base...${NC}"
    "${ALEMBIC_BIN}" downgrade base
    echo -e "${CYAN}[3/3] Re-upgrading to head...${NC}"
    "${ALEMBIC_BIN}" upgrade head
    echo -e "${GREEN}[+] Migration reversibility test passed!${NC}"
else
    echo -e "${YELLOW}Usage: ./scripts/db-migrate.sh [upgrade|downgrade|revision|current|history|check|test]${NC}"
    exit 1
fi

echo -e "${GREEN}[+] Database operation completed successfully!${NC}"


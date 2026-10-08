#!/usr/bin/env bash
# ==============================================================================
# KEEP — Database Seeding Automation Script
# Usage: ./scripts/db-seed.sh [--docker|--native]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="native"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --docker)
            MODE="docker"
            shift
            ;;
        --native)
            MODE="native"
            shift
            ;;
        *)
            echo -e "${RED}[!] Unknown option: $1${NC}"
            echo "Usage: ./scripts/db-seed.sh [--docker|--native]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Database Seeding Engine (Mode: ${MODE})                  ${NC}"
echo -e "${CYAN}================================================================${NC}"

if [ "${MODE}" == "docker" ]; then
    echo -e "${GREEN}[+] Running database seed inside keep-backend container...${NC}"
    docker compose exec keep-backend python -m backend.app.db.seed
else
    cd "${ROOT_DIR}"
    
    # Locate virtual environment python
    PYTHON_BIN="python3"
    if [ -f "${ROOT_DIR}/backend/.venv/bin/python" ]; then
        PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
    elif [ -f "${ROOT_DIR}/.venv/bin/python" ]; then
        PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
    fi

    echo -e "${GREEN}[+] Executing seed engine with ${PYTHON_BIN}...${NC}"
    PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/backend" "${PYTHON_BIN}" -m backend.app.db.seed
fi

echo -e "${GREEN}[+] Database seeding completed successfully!${NC}"

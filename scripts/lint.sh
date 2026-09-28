#!/usr/bin/env bash
# ==============================================================================
# KEEP — Monorepo Linting Runner
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Running KEEP Code Quality & Linting Verification              ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Python Linting
echo -e "\n${CYAN}[1/2] Checking Python code quality...${NC}"
if command -v ruff &> /dev/null; then
    ruff check backend/ tests/
else
    echo -e "${YELLOW}[i] ruff not found in PATH, running python compile check...${NC}"
    python3 -m py_compile backend/app/main.py backend/app/core/config.py backend/app/core/logging.py
fi

# Frontend Linting
echo -e "\n${CYAN}[2/2] Checking Frontend code quality (ESLint)...${NC}"
cd "${ROOT_DIR}/frontend"
npm run lint

echo -e "\n${GREEN}[+] All linting checks passed!${NC}"

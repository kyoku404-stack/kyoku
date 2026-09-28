#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Backend Test Suite
# Usage: ./scripts/test-backend.sh [unit|integration|all]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}"

SUITE="${1:-all}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Running KEEP Backend Test Suite (${SUITE})                      ${NC}"
echo -e "${CYAN}================================================================${NC}"

if command -v pytest &> /dev/null; then
    if [ "${SUITE}" == "unit" ]; then
        pytest tests/unit/ -v
    elif [ "${SUITE}" == "integration" ]; then
        pytest tests/integration/ -v
    else
        pytest tests/unit/ tests/integration/ -v
    fi
else
    echo -e "${YELLOW}[i] pytest not found in PATH, using python3 -m unittest...${NC}"
    if [ "${SUITE}" == "unit" ]; then
        python3 -m unittest discover -s tests/unit -p "test_*.py" -v
    elif [ "${SUITE}" == "integration" ]; then
        python3 -m unittest discover -s tests/integration -p "test_*.py" -v
    else
        echo -e "${CYAN}--> Running Unit Tests:${NC}"
        python3 -m unittest discover -s tests/unit -p "test_*.py" -v
        echo -e "${CYAN}--> Running Integration Tests:${NC}"
        python3 -m unittest discover -s tests/integration -p "test_*.py" -v
    fi
fi

echo -e "${GREEN}[+] Backend tests completed successfully!${NC}"

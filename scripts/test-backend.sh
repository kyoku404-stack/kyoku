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

# Detect virtualenv pytest binary or fall back to system
PYTEST_CMD=""
if [ -f "${ROOT_DIR}/backend/.venv/bin/pytest" ]; then
    PYTEST_CMD="${ROOT_DIR}/backend/.venv/bin/pytest"
elif [ -f "${ROOT_DIR}/.venv/bin/pytest" ]; then
    PYTEST_CMD="${ROOT_DIR}/.venv/bin/pytest"
elif command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
fi

PYTHON_CMD="python3"
if [ -f "${ROOT_DIR}/backend/.venv/bin/python" ]; then
    PYTHON_CMD="${ROOT_DIR}/backend/.venv/bin/python"
elif [ -f "${ROOT_DIR}/.venv/bin/python" ]; then
    PYTHON_CMD="${ROOT_DIR}/.venv/bin/python"
fi

if [ -n "${PYTEST_CMD}" ]; then
    if [ "${SUITE}" == "unit" ]; then
        "${PYTEST_CMD}" tests/unit/ -v
    elif [ "${SUITE}" == "integration" ]; then
        "${PYTEST_CMD}" tests/integration/ -v
    else
        "${PYTEST_CMD}" tests/unit/ tests/integration/ -v
    fi
else
    echo -e "${YELLOW}[i] pytest not found in PATH or venv, using ${PYTHON_CMD} -m unittest...${NC}"
    if [ "${SUITE}" == "unit" ]; then
        "${PYTHON_CMD}" -m unittest discover -s tests/unit -p "test_*.py" -v
    elif [ "${SUITE}" == "integration" ]; then
        "${PYTHON_CMD}" -m unittest discover -s tests/integration -p "test_*.py" -v
    else
        echo -e "${CYAN}--> Running Unit Tests:${NC}"
        "${PYTHON_CMD}" -m unittest discover -s tests/unit -p "test_*.py" -v
        echo -e "${CYAN}--> Running Integration Tests:${NC}"
        "${PYTHON_CMD}" -m unittest discover -s tests/integration -p "test_*.py" -v
    fi
fi

echo -e "${GREEN}[+] Backend tests completed successfully!${NC}"

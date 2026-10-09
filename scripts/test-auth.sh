#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Phase 1.4 Authentication & Identity Security Test Suites
# Usage: ./scripts/test-auth.sh
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}"
export ENVIRONMENT="test"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP — Phase 1.4 Authentication & Identity Test Runner         ${NC}"
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

if [ -n "${PYTEST_CMD}" ]; then
    echo -e "${CYAN}[1/4] Running Auth Cryptography & RBAC Unit Tests...${NC}"
    "${PYTEST_CMD}" tests/unit/test_auth_security.py -v

    echo -e "${CYAN}[2/4] Running Auth AI Security Contracts Unit Tests...${NC}"
    "${PYTEST_CMD}" tests/unit/test_auth_ai_security_contracts.py -v

    echo -e "${CYAN}[3/4] Running Auth Endpoints Lifecycle Integration Tests...${NC}"
    "${PYTEST_CMD}" tests/integration/test_auth_endpoints.py -v

    echo -e "${CYAN}[4/4] Running Tenant Isolation & Performance Benchmarks...${NC}"
    "${PYTEST_CMD}" tests/integration/test_auth_security_isolation.py tests/integration/test_auth_performance.py -v
else
    echo -e "${YELLOW}[!] Python virtual environment not detected.${NC}"
    exit 1
fi

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✓ ALL AUTHENTICATION & SECURITY TESTS PASSED CLEANLY          ${NC}"
echo -e "${GREEN}================================================================${NC}"

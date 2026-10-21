#!/usr/bin/env bash
# ==============================================================================
# KEEP — Phase 1.8 Document Management & Storage Test Orchestrator
# Executes backend endpoints, storage security, performance benchmarks, and UI tests
# Usage: ./scripts/test-document-management.sh [all|security|perf|backend|unit|frontend|e2e]
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODE="${1:-all}"
PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python3"
PYTEST_BIN="${ROOT_DIR}/backend/.venv/bin/pytest"

if [ ! -f "${PYTEST_BIN}" ]; then
    PYTEST_BIN="pytest"
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Phase 1.8 Document Management & Storage Test Suite       ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Target suite: ${MODE}${NC}"

run_security() {
    echo -e "\n${YELLOW}>>> [1/4] Running Storage Security & Isolation Integration Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_document_storage_security.py -v
}

run_perf() {
    echo -e "\n${YELLOW}>>> [2/4] Running Storage Latency, Performance & Stress Benchmarks...${NC}"
    "${PYTEST_BIN}" tests/integration/test_document_storage_performance.py -v -s
}

run_backend() {
    echo -e "\n${YELLOW}>>> [3/4] Running Document Management REST API Integration Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_document_management_endpoints.py -v
}

run_unit() {
    echo -e "\n${YELLOW}>>> Running Backend Unit Tests...${NC}"
    "${PYTEST_BIN}" tests/unit/ -v
}

run_frontend() {
    echo -e "\n${YELLOW}>>> [4/4] Running Frontend Unit Tests (Vitest)...${NC}"
    npm --prefix frontend test -- --run
}

run_e2e() {
    echo -e "\n${YELLOW}>>> Running Playwright E2E Tests (document_management.spec.ts)...${NC}"
    npx playwright test tests/e2e/document_management.spec.ts
}

case "${MODE}" in
    security)
        run_security
        ;;
    perf)
        run_perf
        ;;
    backend)
        run_backend
        ;;
    unit)
        run_unit
        ;;
    frontend)
        run_frontend
        ;;
    e2e)
        run_e2e
        ;;
    all)
        START_TIME="$(date +%s)"
        run_security
        run_perf
        run_backend
        run_frontend
        END_TIME="$(date +%s)"
        ELAPSED=$((END_TIME - START_TIME))
        echo -e "\n${GREEN}================================================================${NC}"
        echo -e "${GREEN}  ✓ All Phase 1.8 Storage & Document Test Suites Passed! (${ELAPSED}s)  ${NC}"
        echo -e "${GREEN}================================================================${NC}"
        ;;
    *)
        echo -e "${RED}[!] Unknown mode: ${MODE}${NC}"
        echo "Usage: $0 [all|security|perf|backend|unit|frontend|e2e]"
        exit 1
        ;;
esac

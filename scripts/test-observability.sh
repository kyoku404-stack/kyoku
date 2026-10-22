#!/usr/bin/env bash
# ==============================================================================
# KEEP — Phase 1.9 Observability & System Monitoring Test Orchestrator
# Executes Prometheus metrics, multi-tier health probes, performance benchmarks, and UI tests
# Usage: ./scripts/test-observability.sh [all|infra|perf|health|backend|frontend|e2e]
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
PYTEST_BIN="${ROOT_DIR}/backend/.venv/bin/pytest"

if [ ! -f "${PYTEST_BIN}" ]; then
    PYTEST_BIN="pytest"
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Phase 1.9 Observability, Monitoring & Health Test Suite  ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Target suite: ${MODE}${NC}"

run_infra() {
    echo -e "\n${YELLOW}>>> [1/4] Running Observability Infrastructure & Metrics Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_observability_infrastructure.py -v
}

run_perf() {
    echo -e "\n${YELLOW}>>> [2/4] Running Observability Performance & Registry Concurrency Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_observability_performance.py -v -s
}

run_health() {
    echo -e "\n${YELLOW}>>> [3/4] Running Multi-Tier Health Probes & Endpoint Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_health_and_observability_endpoints.py -v
}

run_backend() {
    echo -e "\n${YELLOW}>>> Running All Phase 1.9 Backend Tests...${NC}"
    "${PYTEST_BIN}" tests/unit/test_structured_logging.py \
                    tests/unit/test_metrics_registry.py \
                    tests/unit/test_observability_ai_contracts.py \
                    tests/integration/test_health_and_observability_endpoints.py \
                    tests/integration/test_observability_infrastructure.py \
                    tests/integration/test_observability_performance.py -v
}

run_frontend() {
    echo -e "\n${YELLOW}>>> [4/4] Running Observability Frontend Unit & Component Tests...${NC}"
    npm --prefix frontend test -- src/tests/observabilityService.test.ts src/tests/observabilityComponents.test.tsx --run
}

run_e2e() {
    echo -e "\n${YELLOW}>>> Running Playwright E2E Tests (observability.spec.ts)...${NC}"
    npx playwright test tests/e2e/observability.spec.ts
}

case "${MODE}" in
    infra)
        run_infra
        ;;
    perf)
        run_perf
        ;;
    health)
        run_health
        ;;
    backend)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    e2e)
        run_e2e
        ;;
    all)
        START_TIME="$(date +%s)"
        run_infra
        run_perf
        run_health
        run_frontend
        END_TIME="$(date +%s)"
        ELAPSED=$((END_TIME - START_TIME))
        echo -e "\n${GREEN}================================================================${NC}"
        echo -e "${GREEN}  ✓ All Phase 1.9 Observability & Health Test Suites Passed! (${ELAPSED}s)  ${NC}"
        echo -e "${GREEN}================================================================${NC}"
        ;;
    *)
        echo -e "${RED}[!] Unknown mode: ${MODE}${NC}"
        echo "Usage: $0 [all|infra|perf|health|backend|frontend|e2e]"
        exit 1
        ;;
esac

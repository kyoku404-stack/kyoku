#!/usr/bin/env bash
# ==============================================================================
# KEEP — Phase 1.10 Deployment, Infrastructure & Production Readiness Test Orchestrator
# Executes production infrastructure validation, deployment contracts, and smoke tests
# Usage: ./scripts/test-deployment.sh [all|infra|backend|frontend|e2e]
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
echo -e "${CYAN}  KEEP Phase 1.10 Deployment, Infrastructure & Readiness Suite ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[*] Target suite: ${MODE}${NC}"

run_infra() {
    echo -e "\n${YELLOW}>>> [1/4] Running Deployment Infrastructure & Configuration Tests...${NC}"
    "${PYTEST_BIN}" tests/integration/test_production_deployment_infrastructure.py -v
}

run_backend() {
    echo -e "\n${YELLOW}>>> [2/4] Running Production Backend Configuration & Readiness Tests...${NC}"
    "${PYTEST_BIN}" tests/unit/test_production_backend_config.py \
                    tests/unit/test_deployment_ai_readiness.py \
                    tests/integration/test_production_backend_readiness.py \
                    tests/integration/test_production_deployment_infrastructure.py -v
}

run_frontend() {
    echo -e "\n${YELLOW}>>> [3/4] Running Frontend Production Readiness & Bundle Tests...${NC}"
    npm --prefix frontend test -- src/tests/productionFrontendReadiness.test.tsx --run
}

run_docker() {
    echo -e "\n${YELLOW}>>> [4/4] Validating Docker Compose Production Syntax...${NC}"
    SECRET_KEY="test_secret_for_validation_only_32_chars" \
    POSTGRES_PASSWORD="test_postgres_password" \
    GRAFANA_ADMIN_PASSWORD="test_grafana_password" \
    docker compose -f docker-compose.prod.yml config > /dev/null
    echo -e "${GREEN}[✓] docker-compose.prod.yml configuration is valid!${NC}"
}

case "${MODE}" in
    infra)
        run_infra
        ;;
    backend)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    docker)
        run_docker
        ;;
    all)
        run_infra
        run_backend
        run_frontend
        run_docker
        echo -e "\n${GREEN}================================================================${NC}"
        echo -e "${GREEN}  ✓ ALL Phase 1.10 Deployment & Infrastructure Tests PASSED!   ${NC}"
        echo -e "${GREEN}================================================================${NC}"
        ;;
    *)
        echo -e "${RED}[!] Invalid mode: ${MODE}. Available options: all, infra, backend, frontend, docker${NC}"
        exit 1
        ;;
esac

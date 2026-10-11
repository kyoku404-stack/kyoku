#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Phase 1.5 Organization, Workspace & Multi-Tenant Test Suites
# Member 4 (DevOps & Integration Lead) deliverable
#
# Usage:
#   ./scripts/test-org.sh              # Run all org test suites
#   ./scripts/test-org.sh audit        # Run only audit logging tests
#   ./scripts/test-org.sh isolation    # Run only multi-tenant isolation tests
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}") /.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}"
export ENVIRONMENT="test"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP — Phase 1.5 Organization & Workspace Test Runner         ${NC}"
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

if [ -z "${PYTEST_CMD}" ]; then
    echo -e "${RED}[ERROR] pytest binary not found. Activate the virtual environment first.${NC}"
    exit 1
fi

MODE="${1:-all}"

run_suite() {
    local label="$1"
    local files="$2"
    echo -e "${CYAN}${label}${NC}"
    # shellcheck disable=SC2086
    "${PYTEST_CMD}" ${files} -v
}

case "${MODE}" in
  audit)
    run_suite "[audit] Audit Logging Integration Tests" \
        "tests/integration/test_organization_audit_logging.py"
    ;;
  isolation)
    run_suite "[isolation] Multi-Tenant Isolation Tests" \
        "tests/integration/test_organization_multi_tenant_isolation.py"
    ;;
  hierarchy)
    run_suite "[hierarchy] Org Hierarchy Endpoint Tests" \
        "tests/integration/test_organization_hierarchy_endpoints.py"
    ;;
  seed)
    run_suite "[seed] Database Seeding Integration Tests" \
        "tests/integration/test_db_seeding.py"
    ;;
  all|*)
    echo -e "${CYAN}[1/5] Database Seeding Tests...${NC}"
    "${PYTEST_CMD}" tests/integration/test_db_seeding.py -v

    echo -e "${CYAN}[2/5] Organization Hierarchy Endpoint Tests...${NC}"
    "${PYTEST_CMD}" tests/integration/test_organization_hierarchy_endpoints.py -v

    echo -e "${CYAN}[3/5] Audit Logging Integration Tests...${NC}"
    "${PYTEST_CMD}" tests/integration/test_organization_audit_logging.py -v

    echo -e "${CYAN}[4/5] Multi-Tenant Isolation & RBAC Security Tests...${NC}"
    "${PYTEST_CMD}" tests/integration/test_organization_multi_tenant_isolation.py -v

    echo -e "${CYAN}[5/5] Workspace AI Contracts (if present)...${NC}"
    if [ -f "tests/unit/test_workspace_ai_contracts.py" ]; then
        "${PYTEST_CMD}" tests/unit/test_workspace_ai_contracts.py -v
    else
        echo -e "${YELLOW}  [skip] tests/unit/test_workspace_ai_contracts.py not found${NC}"
    fi
    ;;
esac

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✓ PHASE 1.5 ORGANIZATION TESTS COMPLETED SUCCESSFULLY        ${NC}"
echo -e "${GREEN}================================================================${NC}"

#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run All Test Suites Across Monorepo
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Full-Stack Monorepo Verification & Test Runner           ${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "\n${CYAN}[1/2] Running Backend Test Suites...${NC}"
if ./scripts/test-backend.sh all; then
    echo -e "${GREEN}✓ Backend tests passed.${NC}"
else
    echo -e "${RED}✗ Backend tests failed.${NC}"
    exit 1
fi

echo -e "\n${CYAN}[2/2] Running Frontend Test Suites...${NC}"
if ./scripts/test-frontend.sh; then
    echo -e "${GREEN}✓ Frontend tests passed.${NC}"
else
    echo -e "${RED}✗ Frontend tests failed.${NC}"
    exit 1
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✓ ALL MONOREPO TEST SUITES PASSED CLEANLY (100% SUCCESS)      ${NC}"
echo -e "${GREEN}================================================================${NC}"

#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Frontend Test Suite & Typecheck
# Usage: ./scripts/test-frontend.sh
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/frontend"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Running KEEP Frontend Tests & TypeScript Type Check           ${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "${CYAN}[1/2] Running TypeScript strict typecheck...${NC}"
if [ -f "./node_modules/.bin/tsc" ]; then
    ./node_modules/.bin/tsc --noEmit
else
    npx --yes typescript tsc --noEmit
fi

echo -e "${CYAN}[2/2] Running Vitest unit test suite...${NC}"
npm test

echo -e "${GREEN}[+] Frontend test suite and type check passed!${NC}"

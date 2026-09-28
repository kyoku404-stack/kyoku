#!/usr/bin/env bash
# ==============================================================================
# KEEP — Monorepo Code Formatter
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Formatting KEEP Monorepo Codebase                             ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Format Python
echo -e "\n${CYAN}[1/2] Formatting Python code with ruff / black...${NC}"
if command -v ruff &> /dev/null; then
    ruff format backend/ tests/
else
    echo -e "${YELLOW}[i] ruff formatter not available in PATH, skipping...${NC}"
fi

# Format Frontend
echo -e "\n${CYAN}[2/2] Formatting Frontend with Prettier / ESLint...${NC}"
cd "${ROOT_DIR}/frontend"
if npx prettier --version &> /dev/null; then
    npx prettier --write "src/**/*.{ts,tsx,css,json}"
else
    npm run lint -- --fix
fi

echo -e "\n${GREEN}[+] Formatting complete!${NC}"

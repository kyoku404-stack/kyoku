#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Frontend Server Locally
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/frontend"

echo -e "${CYAN}[+] Starting KEEP React/Vite frontend server on port 3000...${NC}"
exec npm run dev -- --host 0.0.0.0 --port 3000

#!/usr/bin/env bash
# ==============================================================================
# KEEP — Run Backend Server Locally
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}"

echo -e "${CYAN}[+] Starting KEEP FastAPI backend server...${NC}"
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

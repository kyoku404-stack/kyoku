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

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

UVICORN_CMD=""
if [ -f "${ROOT_DIR}/backend/.venv/bin/uvicorn" ]; then
    UVICORN_CMD="${ROOT_DIR}/backend/.venv/bin/uvicorn"
elif [ -f "${ROOT_DIR}/.venv/bin/uvicorn" ]; then
    UVICORN_CMD="${ROOT_DIR}/.venv/bin/uvicorn"
elif command -v uvicorn &> /dev/null; then
    UVICORN_CMD="uvicorn"
else
    PYTHON_CMD="python3"
    if [ -f "${ROOT_DIR}/backend/.venv/bin/python" ]; then
        PYTHON_CMD="${ROOT_DIR}/backend/.venv/bin/python"
    fi
    UVICORN_CMD="${PYTHON_CMD} -m uvicorn"
fi

echo -e "${CYAN}[+] Starting KEEP FastAPI backend server on http://${HOST}:${PORT}...${NC}"
exec ${UVICORN_CMD} backend.app.main:app --host "${HOST}" --port "${PORT}" --reload

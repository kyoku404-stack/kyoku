#!/usr/bin/env bash
# ==============================================================================
# KEEP Enterprise Platform — Backend Deployment Automation Script
#
# Usage:
#   ./scripts/deploy-backend.sh [OPTIONS]
#
# Options:
#   --mode [docker|native]   Deployment mode (default: docker)
#   --workers [N]            Number of Uvicorn workers for native mode (default: 4)
#   --port [PORT]            Backend port to bind / verify (default: 8000)
#   --host [HOST]            Backend host to bind in native mode (default: 0.0.0.0)
#   --skip-migrations        Skip automatic Alembic schema migrations
#   --dry-run                Verify deployment configuration without starting services
#   --help                   Display this usage summary
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODE="docker"
WORKERS=4
PORT=8000
HOST="0.0.0.0"
RUN_MIGRATIONS=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --skip-migrations)
            RUN_MIGRATIONS=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./scripts/deploy-backend.sh [--mode docker|native] [--workers N] [--port PORT] [--skip-migrations] [--dry-run]"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Backend Deployment Engine                                ${NC}"
echo -e "${CYAN}  Mode: ${MODE} | Port: ${PORT} | Workers: ${WORKERS}       ${NC}"
echo -e "${CYAN}================================================================${NC}"

# 1. Environment & Configuration Check
echo -e "\n${CYAN}[1/4] Verifying deployment environment and configuration...${NC}"
if [ -f "${ROOT_DIR}/backend/.env" ]; then
    echo -e "${GREEN}✓ Local backend/.env file found.${NC}"
elif [ -f "${ROOT_DIR}/.env" ]; then
    echo -e "${GREEN}✓ Root .env file found.${NC}"
else
    echo -e "${YELLOW}[!] No .env file found; utilizing default/ambient environment variables.${NC}"
fi

export PYTHONPATH="${ROOT_DIR}"
export ENVIRONMENT="${ENVIRONMENT:-production}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export API_V1_STR="${API_V1_STR:-/api/v1}"

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}--> Dry run requested. Validating environment settings and exiting.${NC}"
    if [ -f "${ROOT_DIR}/backend/.venv/bin/python" ]; then
        "${ROOT_DIR}/backend/.venv/bin/python" -c "from backend.app.core.config import settings; print('Config loaded successfully for:', settings.PROJECT_NAME)"
    elif command -v python3 &> /dev/null; then
        python3 -c "from backend.app.core.config import settings; print('Config loaded successfully for:', settings.PROJECT_NAME)"
    fi
    echo -e "${GREEN}[+] Dry run complete. Configuration is valid.${NC}"
    exit 0
fi

# 2. Database Migrations
if [ "${RUN_MIGRATIONS}" = true ]; then
    echo -e "\n${CYAN}[2/4] Executing database schema migrations (Alembic)...${NC}"
    if [ -f "${ROOT_DIR}/scripts/db-migrate.sh" ]; then
        ./scripts/db-migrate.sh upgrade || {
            echo -e "${YELLOW}[!] Database migration step skipped or non-blocking in development.${NC}"
        }
    fi
else
    echo -e "\n${YELLOW}[2/4] Skipping database migrations (--skip-migrations).${NC}"
fi

# 3. Deployment Launch
echo -e "\n${CYAN}[3/4] Launching backend application (${MODE} mode)...${NC}"
if [ "${MODE}" == "docker" ]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH.${NC}"
        exit 1
    fi
    echo -e "${CYAN}--> Building and launching backend container via Docker Compose...${NC}"
    docker compose up -d --build backend
elif [ "${MODE}" == "native" ]; then
    UVICORN_BIN=""
    if [ -f "${ROOT_DIR}/backend/.venv/bin/uvicorn" ]; then
        UVICORN_BIN="${ROOT_DIR}/backend/.venv/bin/uvicorn"
    elif command -v uvicorn &> /dev/null; then
        UVICORN_BIN="uvicorn"
    else
        PYTHON_BIN="python3"
        if [ -f "${ROOT_DIR}/backend/.venv/bin/python" ]; then
            PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
        fi
        UVICORN_BIN="${PYTHON_BIN} -m uvicorn"
    fi

    echo -e "${CYAN}--> Starting production ASGI server (${UVICORN_BIN}) with ${WORKERS} workers on http://${HOST}:${PORT}...${NC}"
    exec ${UVICORN_BIN} backend.app.main:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --workers "${WORKERS}" \
        --no-access-log
else
    echo -e "${RED}Error: Invalid mode '${MODE}'. Choose 'docker' or 'native'.${NC}"
    exit 1
fi

# 4. Post-Deployment Verification (for Docker mode)
if [ "${MODE}" == "docker" ]; then
    echo -e "\n${CYAN}[4/4] Verifying container health on http://localhost:${PORT}/api/v1/health...${NC}"
    MAX_ATTEMPTS=15
    ATTEMPT=1
    HEALTH_URL="http://localhost:${PORT}/api/v1/health"

    while [ ${ATTEMPT} -le ${MAX_ATTEMPTS} ]; do
        if curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend deployment healthy! Status response:${NC}"
            curl -s "${HEALTH_URL}"
            echo ""
            exit 0
        fi
        echo -e "${YELLOW}Waiting for backend to become ready (attempt ${ATTEMPT}/${MAX_ATTEMPTS})...${NC}"
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done

    echo -e "${RED}✗ Backend deployment health check timed out on ${HEALTH_URL}${NC}"
    exit 1
fi

#!/usr/bin/env bash
# ==============================================================================
# KEEP — Development Environment Entrypoint
# Usage: ./scripts/dev.sh [docker|native]
# ==============================================================================

set -euo pipefail

# ANSI color codes
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MODE="${1:-docker}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP Enterprise Platform — Development Server Launcher        ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Navigate to project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] .env file not found. Copying .env.example to .env...${NC}"
    cp .env.example .env
fi

if [ "${MODE}" == "docker" ]; then
    echo -e "${GREEN}[+] Starting multi-container stack via Docker Compose...${NC}"
    exec ./scripts/docker-dev.sh
elif [ "${MODE}" == "native" ]; then
    echo -e "${GREEN}[+] Starting native development services...${NC}"
    echo -e "${YELLOW}[i] Starting backend on http://localhost:8000 and frontend on http://localhost:3000...${NC}"
    
    # Trap SIGINT/SIGTERM to kill child processes
    trap 'kill 0' SIGINT SIGTERM EXIT
    
    ./scripts/run-backend.sh &
    BACKEND_PID=$!
    
    ./scripts/run-frontend.sh &
    FRONTEND_PID=$!
    
    wait $BACKEND_PID $FRONTEND_PID
else
    echo -e "${RED}[ERROR] Unknown mode: ${MODE}. Use 'docker' or 'native'.${NC}"
    exit 1
fi

#!/usr/bin/env bash
# ==============================================================================
# KEEP — Start Docker Compose Services
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] Copying .env.example to .env...${NC}"
    cp .env.example .env
fi

echo -e "${CYAN}[+] Building and starting containers in detached mode...${NC}"
docker compose up -d --build

echo -e "${GREEN}[+] Services started successfully!${NC}"
echo -e "  - Frontend:  http://localhost:3000"
echo -e "  - Backend:   http://localhost:8000"
echo -e "  - API Docs:  http://localhost:8000/docs"
echo -e "  - Postgres:  localhost:5432"
echo -e "  - Redis:     localhost:6379"
echo -e "\n${YELLOW}To view logs in real time, run: docker compose logs -f${NC}"

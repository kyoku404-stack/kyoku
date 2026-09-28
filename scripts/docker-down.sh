#!/usr/bin/env bash
# ==============================================================================
# KEEP — Stop Docker Compose Services
# Usage: ./scripts/docker-down.sh [--volumes]
# ==============================================================================

set -euo pipefail

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ "${1:-}" == "--volumes" || "${1:-}" == "-v" ]]; then
    echo -e "${YELLOW}[!] Stopping containers and removing persistent volumes...${NC}"
    docker compose down -v --remove-orphans
else
    echo -e "${YELLOW}[!] Stopping containers...${NC}"
    docker compose down --remove-orphans
fi

echo -e "${GREEN}[+] Docker services stopped.${NC}"

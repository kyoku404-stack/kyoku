#!/usr/bin/env bash
# ==============================================================================
# KEEP — End-to-End System Health & Service Readiness Check
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:3000}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  KEEP System Health & Integration Verification                 ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check Backend API
echo -e "\n${CYAN}[1/5] Testing Backend API Root Discovery (${BACKEND_URL}/)...${NC}"
if curl -s -f "${BACKEND_URL}/" > /dev/null; then
    ROOT_RES=$(curl -s "${BACKEND_URL}/")
    echo -e "${GREEN}✓ Backend Root OK:${NC} ${ROOT_RES}"
else
    echo -e "${RED}✗ Backend Root unreachable on ${BACKEND_URL}/${NC}"
fi

echo -e "\n${CYAN}[2/5] Testing Backend Health Check (${BACKEND_URL}/api/v1/health)...${NC}"
if curl -s -f "${BACKEND_URL}/api/v1/health" > /dev/null; then
    HEALTH_RES=$(curl -s "${BACKEND_URL}/api/v1/health")
    echo -e "${GREEN}✓ Backend Health OK:${NC} ${HEALTH_RES}"
else
    echo -e "${RED}✗ Backend Health endpoint unreachable on ${BACKEND_URL}/api/v1/health${NC}"
fi

echo -e "\n${CYAN}[3/5] Testing Backend Diagnostic Details (${BACKEND_URL}/api/v1/health/details)...${NC}"
if curl -s -f "${BACKEND_URL}/api/v1/health/details" > /dev/null; then
    DETAILS_RES=$(curl -s "${BACKEND_URL}/api/v1/health/details")
    echo -e "${GREEN}✓ Backend Diagnostic Details OK:${NC} ${DETAILS_RES}"
else
    echo -e "${RED}✗ Backend Diagnostic Details unreachable on ${BACKEND_URL}/api/v1/health/details${NC}"
fi

echo -e "\n${CYAN}[4/5] Testing OpenAPI Documentation Specification (${BACKEND_URL}/api/v1/openapi.json)...${NC}"
if curl -s -f "${BACKEND_URL}/api/v1/openapi.json" > /dev/null; then
    OPENAPI_TITLE=$(curl -s "${BACKEND_URL}/api/v1/openapi.json" | grep -o '"title":"[^"]*"' | head -n 1 || echo '"title":"KEEP"')
    echo -e "${GREEN}✓ OpenAPI Schema OK:${NC} ${OPENAPI_TITLE}"
else
    echo -e "${RED}✗ OpenAPI Schema unreachable on ${BACKEND_URL}/api/v1/openapi.json${NC}"
fi

echo -e "\n${CYAN}[5/5] Testing Frontend Web Server (${FRONTEND_URL}/)...${NC}"
if curl -s -I "${FRONTEND_URL}/" | head -n 1 | grep -E "200|304" > /dev/null; then
    echo -e "${GREEN}✓ Frontend Server OK on ${FRONTEND_URL}/${NC}"
else
    echo -e "${YELLOW}[!] Frontend Server not responding on ${FRONTEND_URL}/ (may not be running)${NC}"
fi

echo -e "\n${CYAN}================================================================${NC}"

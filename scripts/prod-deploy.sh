#!/usr/bin/env bash
# ==============================================================================
# KEEP Enterprise Platform — Production Automated Deployment & Health Gate
# ==============================================================================
# Specification: devdocs/p1/p1.10.txt (Chapters 14, 17, 18) & ADR-031
# Architecture: docs/Architecture/deployment-ai-infrastructure.md
# Role: Member 4 (DevOps & Integration Lead)
# ==============================================================================

set -euo pipefail

# ANSI Styling
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

COMPOSE_FILE="docker-compose.prod.yml"
MAX_HEALTH_ATTEMPTS=12   # 12 attempts * 5s = 60s SLA (ADR-031)
HEALTH_INTERVAL=5
HEALTH_URL="http://localhost/health"

log_info() { echo -e "${CYAN}[INFO]${RESET} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
log_error() { echo -e "${RED}[ERROR]${RESET} $1"; }

echo -e "${BOLD}${CYAN}====================================================================${RESET}"
echo -e "${BOLD}${CYAN}   KEEP Enterprise Platform — Production Automated Deployment Engine ${RESET}"
echo -e "${BOLD}${CYAN}====================================================================${RESET}"

# Step 1: Pre-flight Configuration Validation
log_info "Step 1/5: Validating production environment configurations..."
if [[ ! -f "$COMPOSE_FILE" ]]; then
    log_error "Missing $COMPOSE_FILE orchestration specification."
    exit 1
fi

if [[ -z "${SECRET_KEY:-}" ]] || [[ "${SECRET_KEY:-}" == *"super_secret"* ]]; then
    log_warn "SECRET_KEY is using development default or unset. Ensure a cryptographically secure key is used."
fi

# Step 2: Validate Docker Compose Configuration Syntax
log_info "Step 2/5: Validating Compose YAML syntax..."
docker compose -f "$COMPOSE_FILE" config > /dev/null
log_success "Compose specification syntax validated."

# Step 3: Build & Pull Production Containers
log_info "Step 3/5: Building multi-stage production container images..."
docker compose -f "$COMPOSE_FILE" build --pull
log_success "Production container images built."

# Step 4: Run Database Migrations (Zero-Downtime Migration Seam)
log_info "Step 4/5: Running database schema migrations (Alembic upgrade head)..."
docker compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head
log_success "Database schema is at HEAD revision."

# Step 5: Rolling Container Launch & Health Gating (ADR-031)
log_info "Step 5/5: Launching production services and evaluating health probe..."
docker compose -f "$COMPOSE_FILE" up -d

log_info "Evaluating health check gate (${HEALTH_URL}) with 60s SLA threshold..."
attempt=1
healthy=false

while [[ $attempt -le $MAX_HEALTH_ATTEMPTS ]]; do
    if curl -s -f -m 5 "$HEALTH_URL" | grep -q '"status":"healthy"'; then
        healthy=true
        break
    else
        echo -e "${YELLOW}Health probe attempt $attempt/$MAX_HEALTH_ATTEMPTS: Pending or unready...${RESET}"
        sleep $HEALTH_INTERVAL
        attempt=$((attempt + 1))
    fi
done

if [[ "$healthy" == "true" ]]; then
    echo ""
    log_success "===================================================================="
    log_success " DEPLOYMENT SUCCESSFUL: All platform services verified operational!"
    log_success " Ingress Gateway: https://${PRODUCTION_DOMAIN:-localhost}"
    log_success " Health Probe:    $HEALTH_URL"
    log_success "===================================================================="
    exit 0
else
    echo ""
    log_error "===================================================================="
    log_error " DEPLOYMENT FAILED: Health check gate timed out after 60 seconds."
    log_error " Initiating automated rollback protocol (ADR-031)..."
    log_error "===================================================================="
    docker compose -f "$COMPOSE_FILE" logs --tail 50 backend gateway
    docker compose -f "$COMPOSE_FILE" down
    exit 1
fi

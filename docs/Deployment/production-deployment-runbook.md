# KEEP — Master Production Deployment, Infrastructure & Operations Runbook

> **Specification Source:** `devdocs/p1/p1.10.txt` (Chapters 1–20)  
> **Architecture Reference:** `docs/Architecture/deployment-ai-infrastructure.md` & `ADR-029`, `ADR-030`, `ADR-031`  
> **Role Owner:** Member 4 (DevOps & Integration Lead)  
> **Target Environment:** Multi-Container Production Host (Linux Ubuntu 22.04 / 24.04 LTS, Docker Engine 26+, Compose v2.27+)

---

## 1. Production Architecture Overview

The KEEP Enterprise platform deploys as an isolated, containerized multi-tier monorepo behind an enterprise Nginx reverse proxy gateway terminating TLS 1.3/1.2:

```
                            [ Public Internet ]
                                     │
                     HTTPS 443 / TLS 1.3 / Port 80 Redirect
                                     ▼
                   ┌───────────────────────────────────┐
                   │   Nginx Gateway (keep-gateway)    │
                   │    TLS Termination & Rate Limits  │
                   └─────────────────┬─────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
  ┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
  │  keep-frontend   │    │     keep-backend    │    │ keep-prometheus  │
  │ (Static on Nginx)│    │  (FastAPI + Uvicorn)│    │ (Internal Only)  │
  │    Port: 3000    │    │     Port: 8000      │    │    Port: 9090    │
  └──────────────────┘    └──────────┬──────────┘    └──────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
         ┌─────────────────────┐           ┌─────────────────────┐
         │    keep-postgres    │           │     keep-redis      │
         │ (pg16 + pgvector)   │           │    (Cache & AOF)    │
         │     Port: 5432      │           │     Port: 6379      │
         └─────────────────────┘           └─────────────────────┘
```

---

## 2. Infrastructure Sizing & Container Resource Limits

| Service Container | Image / Base | Internal Port | Exposed Port | CPU Limit | Memory Limit | Storage Volume |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `keep-gateway` | `nginx:1.27-alpine` | `80`, `443` | `80`, `443` | `0.50` | `256 MB` | `nginx_certs`, `certbot_www` |
| `keep-frontend-prod` | `nginx:1.27-alpine` | `3000` | None (Internal) | `1.00` | `1024 MB` | None (Stateless) |
| `keep-backend-prod` | `python:3.12-slim` | `8000` | None (Internal) | `2.00` | `2048 MB` | `storage_data:/app/storage` |
| `keep-postgres-prod` | `pgvector/pgvector:pg16` | `5432` | None (Internal) | `2.00` | `4096 MB` | `postgres_data:/var/lib/postgresql/data` |
| `keep-redis-prod` | `redis:7-alpine` | `6379` | None (Internal) | `1.00` | `1024 MB` | `redis_data:/data` |
| `keep-prometheus-prod`| `prom/prometheus:v2.54.1`| `9090` | None (Internal) | `0.50` | `1024 MB` | `prometheus_data:/prometheus` |
| `keep-grafana-prod` | `grafana/grafana:11.1.0`| `3000` | `3001` (Admin) | `0.50` | `512 MB` | `grafana_data:/var/lib/grafana` |
| `keep-loki-prod` | `grafana/loki:3.1.0` | `3100` | None (Internal) | `0.50` | `1024 MB` | `loki_data:/loki` |
| `keep-promtail-prod` | `grafana/promtail:3.1.0`| None | None (Internal) | `0.20` | `256 MB` | Docker socket & containers log |

---

## 3. Pre-Flight Server Provisioning & Secrets Setup

### 3.1 Host Prerequisites
- Docker Engine 26.0+ installed and enabled (`sudo systemctl enable --now docker`).
- Docker Compose v2.27+ plugin installed (`docker compose version`).
- Firewall ports `80` (HTTP) and `443` (HTTPS) open. Port `3001` restricted to administrative VPN or IP allowlist.

### 3.2 Production Environment File (`.env.production`)
Create `.env.production` on the production server (chmod 600):
```ini
ENVIRONMENT=production
LOG_LEVEL=INFO
PRODUCTION_DOMAIN=keep.enterprise.io

# Cryptographically Secure Secrets (Generate via `openssl rand -hex 32`)
SECRET_KEY=e8c2a4175b92f7c03d19842a5efbc671092a487cbfa134d9203847a1928374bc
POSTGRES_USER=keep_admin
POSTGRES_PASSWORD=generate_high_entropy_postgres_password_here
POSTGRES_DB=keep_db

# Redis & Token Lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Database Connection Pool Sizing
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
ENABLE_OPENAPI_DOCS=false

# Monitoring Credentials
GRAFANA_ADMIN_USER=enterprise_admin
GRAFANA_ADMIN_PASSWORD=generate_high_entropy_grafana_password_here
```

---

## 4. SSL/TLS Certificate Provisioning

### 4.1 Production (Let's Encrypt / Certbot)
```bash
# Provision certificate using standalone certbot
sudo docker run -it --rm -p 80:80 \
  -v nginx_certs:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d keep.enterprise.io --agree-tos --email admin@enterprise.io
```

### 4.2 Staging / Self-Signed Testing Fallback
```bash
mkdir -p ./infrastructure/nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./infrastructure/nginx/certs/privkey.pem \
  -out ./infrastructure/nginx/certs/fullchain.pem \
  -subj "/CN=localhost/O=KEEP/OU=Engineering"
```

---

## 5. Automated Deployment Workflow (`scripts/prod-deploy.sh`)

Deploying new versions utilizes automated health gating and zero-downtime rolling updates:

```bash
# Execute automated production deployment
chmod +x scripts/*.sh
./scripts/prod-deploy.sh
```

### 5.1 Deployment Phases:
1. **Pre-flight Validation:** Checks `.env.production` variables and verifies Docker Compose YAML syntax.
2. **Container Build:** Builds multi-stage production images (`Dockerfile.backend` and `Dockerfile.frontend` production target).
3. **Database Migration:** Executes `alembic upgrade head` in an isolated ephemeral container against the production PostgreSQL instance.
4. **Service Boot:** Runs `docker compose -f docker-compose.prod.yml up -d` with rolling container replacement.
5. **Health Gate Evaluation (ADR-031):** Polls `http://localhost/health` every 5 seconds for up to 60 seconds.
   - If `/health` returns `status: "healthy"`: Deployment succeeds.
   - If `/health` does not respond within 60s: Deployment triggers automatic rollback (`docker compose down`).

---

## 6. Disaster Recovery & Backup Runbook

### 6.1 Service Level Objectives (SLOs)
- **Recovery Point Objective (RPO):** < 1 hour
- **Recovery Time Objective (RTO):** < 15 minutes

### 6.2 Scheduled Backup Execution (`scripts/prod-backup.sh`)
Cron schedule: Executed hourly at minute 0 (`0 * * * *`):
```bash
# Manual or cron trigger
./scripts/prod-backup.sh
```

Snapshot directory layout:
```
backups/production/snapshot_20261024_120000/
├── manifest.json              # SHA-256 hashes & metadata
├── postgres_database.dump     # Custom-format binary pg_dump
└── storage_volume.tar.gz      # Compressed document storage
```

### 6.3 Disaster Recovery Restoration (`scripts/prod-restore.sh`)
To restore from cold backup after a failure:
```bash
./scripts/prod-restore.sh ./backups/production/snapshot_20261024_120000
```
Restoration executes:
1. Cryptographic SHA-256 integrity validation against `manifest.json`.
2. Safe PostgreSQL database restore using `pg_restore --clean --if-exists`.
3. Tenant document storage uncompression into persistent volume.
4. Alembic schema consistency check and `/health` probe validation.

---

## 7. Incident Response & Monitoring

| Symptom | Diagnosis Command | Remediating Action |
| :--- | :--- | :--- |
| **Backend 502 Bad Gateway** | `docker compose -f docker-compose.prod.yml logs --tail 100 backend` | Check database connectivity; restart backend container |
| **Database Pool Exhaustion** | Query `/health/database` or check Grafana DB Dashboard | Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` in `.env.production` |
| **High API Latency (> 300ms)** | Inspect Grafana P95 panel and Loki logs | Check slow queries in PostgreSQL; review server CPU utilization |
| **Storage Quota Exceeded** | Inspect `/health/storage` or Prometheus `storage_used_bytes` | Run archive retention or expand storage volume |
| **SSL Certificate Expiry** | `openssl x509 -enddate -noout -in /etc/nginx/certs/fullchain.pem` | Run Certbot renew script |

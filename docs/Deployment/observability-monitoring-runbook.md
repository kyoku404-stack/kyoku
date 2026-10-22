# KEEP — Observability, Monitoring & Operations Runbook

> **Specification Source**: `devdocs/p1/p1.9.txt` (Chapters 3, 6, 7, 8, 9, 10, 14, 15, 17, 18)  
> **Phase**: 1.9 — Logging, Monitoring & System Observability  
> **Role**: Member 4 (DevOps & Integration Lead)  
> **Status**: APPROVED & OPERATIONAL  

---

## 1. Executive Summary & Stack Topology

The KEEP Enterprise Platform employs an integrated, multi-layered observability architecture designed for high-throughput AI workloads, multi-tenant persistence, and distributed microservices. The stack provides real-time metric collection, time-series analysis, centralized log aggregation, dynamic threshold alerting, and multi-tier health diagnostics.

```
                    ┌──────────────────────────────────────────────┐
                    │      KEEP FastAPI Backend (/metrics)         │
                    └──────────────┬───────────────────┬───────────┘
                                   │                   │
                        Scrapes Metrics           Emits JSON Logs
                                   │                   │
                                   ▼                   ▼
                    ┌──────────────────────┐  ┌────────────────────┐
                    │  Prometheus (9090)   │  │   Promtail (9080)  │
                    │  Time-Series TSDB    │  │   Log Shipper      │
                    └──────────┬───────────┘  └────────┬───────────┘
                               │                       │
                               │ Alert Rules           │ Push Log Streams
                               ▼                       ▼
                    ┌──────────────────────┐  ┌────────────────────┐
                    │  Alertmanager / Web  │  │    Loki (3100)     │
                    │  Threshold Triggers  │  │    Log Engine      │
                    └──────────┬───────────┘  └────────┬───────────┘
                               │                       │
                               └───────────┬───────────┘
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │      Grafana (3001) / Admin Dashboards       │
                    │      KEEP Frontend Observability (3000)      │
                    └──────────────────────────────────────────────┘
```

---

## 2. Docker Compose Orchestration & Service Matrix

The monitoring services are fully orchestrated via root `docker-compose.yml`:

| Service | Container Name | Image | Port | Volumes | Purpose & Health Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend** | `keep-backend` | `Dockerfile.backend` | `8000:8000` | `storage_data:/app/storage` | REST API, Prometheus exporter (`/metrics`), composite probes (`/health`). |
| **Prometheus** | `keep-prometheus` | `prom/prometheus:v2.54.1` | `9090:9090` | `prometheus_data`, `./infrastructure/prometheus` | Scrapes backend `/metrics` every 5s; evaluates alert rules every 10s. Healthcheck: `/-/healthy`. |
| **Grafana** | `keep-grafana` | `grafana/grafana:11.1.0` | `3001:3000` | `grafana_data`, `./infrastructure/grafana/provisioning` | Auto-provisions Prometheus & Loki datasources and `keep-overview-dashboard.json`. Healthcheck: `/api/health`. |
| **Loki** | `keep-loki` | `grafana/loki:3.1.0` | `3100:3100` | `loki_data`, `./infrastructure/loki/loki-config.yml` | Ingests, indexes, and retains structured logs for 30 days. Healthcheck: `/ready`. |
| **Promtail** | `keep-promtail` | `grafana/promtail:3.1.0` | `9080:9080` | `/var/run/docker.sock`, `./infrastructure/promtail` | Collects stdout container logs, parses canonical JSON fields (`level`, `module`, `action`, `trace_id`), pushes to Loki. |

---

## 3. Prometheus Metric Registry (`/metrics`)

The backend exposes standard Prometheus text exposition format on root `GET /metrics`.

### 3.1 Core Metric Catalog

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | `handler`, `method`, `status` | Cumulative total of HTTP transactions processed by API Gateway. |
| `http_request_duration_seconds` | Histogram | `handler`, `method`, `le` | Request duration latency histogram across 11 buckets (5ms to 10s). |
| `http_requests_in_progress` | Gauge | None | Number of concurrent requests actively executing in the event loop. |
| `db_pool_active_connections` | Gauge | None | Active connections checked out of SQLAlchemy PostgreSQL connection pool. |
| `db_pool_size` | Gauge | None | Configured maximum pool capacity. |
| `storage_used_bytes` | Gauge | None | Total storage footprint across multi-tenant document directories. |
| `storage_capacity_bytes` | Gauge | None | Total storage volume provisioned limit. |
| `auth_login_failures_total` | Counter | None | Cumulative failed authentication attempts for brute-force tracking. |
| `ai_tokens_consumed_total` | Counter | `model`, `operation`, `organization_id` | Token meter tracking input and completion tokens. |
| `ai_operations_total` | Counter | `operation`, `status` | Execution count for embeddings, vector search, LLM completion, and RAG. |
| `process_uptime_seconds` | Gauge | None | Continuous backend process uptime in seconds. |

---

## 4. Alerting Matrix & Operational Runbooks

Alert rules are defined in `infrastructure/prometheus/alert_rules.yml`:

### 4.1 Alert Rules Catalog

| Alert Identifier | Severity | Trigger Threshold | Duration | Runbook Action |
| :--- | :--- | :--- | :--- | :--- |
| `DatabaseOffline` | **CRITICAL** | `db_pool_active_connections < 0` or `up == 0` | 15s | Check `keep-postgres` container status; verify database credentials in `.env`; restart container if needed. |
| `CriticalApiErrorRate` | **CRITICAL** | 5xx error rate > 5.0% | 1m | Inspect structured logs filtered by `level="ERROR"`; trace recent deployments; isolate failing route. |
| `HighApiErrorRate` | **WARNING** | 5xx error rate > 2.0% | 2m | Review incoming payload formats and database query timeouts. |
| `HighLatencyP95` | **WARNING** | p95 latency > 250ms (SLA breach) | 3m | Identify slow database queries; check Redis cache hit ratio; scale backend replicas. |
| `StorageNearCapacity` | **WARNING** | Storage volume utilization > 85% | 5m | Execute `scripts/storage-backup.sh`; purge expired soft-deleted files; plan disk expansion. |
| `StorageCriticalCapacity`| **CRITICAL** | Storage volume utilization > 95% | 2m | Immediate disk expansion required to prevent write lockouts. |
| `DatabasePoolNearExhaustion` | **WARNING** | Active connections > 85% of max | 1m | Check for long-running uncommitted transactions or connection leaks. |
| `BruteForceAttempt` | **SECURITY** | > 10 failed logins per minute | 1m | Inspect IP address; enable IP rate limiting; trigger user account lockouts. |
| `AIRateLimitExceeded` | **WARNING** | > 20 HTTP 429 responses per minute | 2m | Review tenant token quotas and sliding window rate limits. |

---

## 5. Grafana Dashboard Architecture

Pre-provisioned automatically at startup via:
- Datasources: `infrastructure/grafana/provisioning/datasources/datasources.yml`
- Dashboards Provider: `infrastructure/grafana/provisioning/dashboards/dashboards.yml`
- Overview Dashboard: `infrastructure/grafana/dashboards/keep-overview-dashboard.json`

### Dashboard Layout Panels:
1. **Platform Quick KPIs**: Uptime gauge, RPS throughput, P95 latency, 5xx error rate %, DB pool %.
2. **HTTP Traffic & Latency Distribution**: Time-series request rate broken down by HTTP status code (`200`, `201`, `400`, `401`, `403`, `500`), and percentile curves (`p50`, `p95`, `p99`).
3. **Subsystem Persistence & Resource Utilization**: PostgreSQL connection pool gauge, storage used bytes vs capacity gauge, and AI/RAG operation counters.
4. **Live Loki Log Explorer**: Stream of canonical structured JSON logs with search and filter capabilities.

---

## 6. Centralized Structured Logging & LogQL Queries

All logs conform to the canonical 13-field schema specified in `devdocs/p1/p1.9.txt` Chapter 6.

### Common LogQL Queries in Grafana:
- **All Backend Errors**:
  ```logql
  {service="keep-backend"} | json | level="ERROR"
  ```
- **Filter by User or Organization**:
  ```logql
  {service="keep-backend"} | json | organization_id="7ca38f12-2111-4b12-a1b2-1c2d3e4f5a6b"
  ```
- **Trace Specific Request by Request ID**:
  ```logql
  {service="keep-backend"} | json | request_id="req-98f24a1b-312c-47ea-8d19-bca128f73110"
  ```
- **Slow Requests (> 200ms)**:
  ```logql
  {service="keep-backend"} | json | execution_time_ms > 200
  ```

---

## 7. Multi-Tier Health Probe Diagnostic Runbook

| Probe URL | Target Subsystem | Diagnostic Criteria | Expected Latency SLA |
| :--- | :--- | :--- | :--- |
| `GET /health` | Composite System | Verifies database, storage, API, and auth dependencies. | < 25 ms |
| `GET /health/database`| PostgreSQL & pgvector | Executes `SELECT 1`, connection pool count, and pgvector extension status. | < 10 ms |
| `GET /health/storage` | Filesystem Volume | Performs non-blocking write/delete probe to `STORAGE_ROOT`, checks quota and free bytes. | < 5 ms |
| `GET /health/api` | API Gateway Process | Evaluates event loop responsiveness, uptime, and memory RSS footprint. | < 2 ms |
| `GET /health/auth` | Cryptographic Provider| Validates JWT secret key, signature algorithm (`HS256`), and expiration parameters. | < 5 ms |

---

## 8. Automated Test Execution & Verification

To execute all observability test suites:
```bash
# Run full suite (infrastructure, perf, health, frontend)
./scripts/test-observability.sh all

# Target specific subsystem
./scripts/test-observability.sh infra
./scripts/test-observability.sh perf
./scripts/test-observability.sh health
./scripts/test-observability.sh frontend
./scripts/test-observability.sh e2e
```

### Monorepo Test Baseline (Phase 1.9 Completed):
- Backend Tests: **422 / 422 PASSED** (100%)
- Frontend Tests: **180 / 180 PASSED** (100%)
- Total Monorepo Tests: **602 / 602 PASSED** (100%)
- Lint Status: **0 errors, 0 warnings** (Ruff, ESLint, TypeScript `tsc --noEmit`)

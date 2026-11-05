# Architecture Specification: Production Infrastructure, Scalability, Observability & High Availability

> **Phase**: 3.6  
> **Author**: Member 1 (Project Lead & AI Architect)  
> **Status**: DRAFT / APPROVED FOR IMPLEMENTATION  
> **Domain**: `/docs/Architecture/production-infrastructure-scalability-observability.md`  
> **Specification Reference**: `devdocs/p3/p3.6.txt` (Chapters 1–20)

---

## 1. Executive Summary & Architectural Goals

Phase 3.6 transforms the KEEP platform from a high-capability multi-agent platform into a cloud-native, enterprise-grade production platform capable of handling thousands of concurrent enterprise users, millions of multi-modal knowledge objects, and continuous real-time AI workloads with high availability (>= 99.9% uptime SLA) and disaster resilience.

### Core Architectural Goals
1. **Cloud-Native Container Orchestration**: Decouple monolithic responsibilities into discrete, independently autoscalable microservices managed under Kubernetes (EKS / GKE / AKS / On-Premise K8s).
2. **Multi-Region / Multi-AZ High Availability**: Eliminate single points of failure across ingress, gateway, application workers, database persistence, and vector stores with automated health probing, self-healing, and failover.
3. **Multi-Tier Distributed Caching**: Minimize database and LLM compute latency through a Redis 7 cluster layer supporting Session Caching, Auth JWT Caching, AI Response Caching, Vector Search Caching, and Metadata Caching.
4. **Resilient Disaster Recovery (DR)**: Enforce a Recovery Point Objective (RPO) $\le$ 1 hour and Recovery Time Objective (RTO) $\le$ 4 hours via automated PostgreSQL WAL replication, S3/MinIO bucket replication, and automated snapshot verification.
5. **Zero-Downtime Deployment Strategies**: Provide declarative Blue-Green, Canary, and Rolling deployment capabilities with automated health checks, metric gating, and sub-second automated rollback triggers.
6. **Full-Stack Enterprise Observability**: Integrate Prometheus metric instrumentation, Grafana visualization dashboards, structured JSON logging, and distributed tracing across async AI and ingestion pipelines.
7. **Production Operations & Infrastructure APIs**: Expose unified, RBAC-protected system APIs for real-time health diagnostics, live telemetry KPIs, centralized log querying, deployment dispatching, and disaster recovery administration.

---

## 2. High-Level System Architecture

```
                                  [ Internet Users / Enterprise Clients ]
                                                     │
                                                     ▼
                                       [ Layer 7 Cloud Load Balancer ]
                                     (HTTPS / TLS 1.3 Termination, WAF)
                                                     │
                                                     ▼
                                      [ Kubernetes Ingress Controller ]
                                           (Nginx / Traefik / ALB)
                                                     │
                         ┌───────────────────────────┼───────────────────────────┐
                         ▼                           ▼                           ▼
                [ Frontend SPA Pods ]      [ API Gateway / Backend ]   [ AI & Ingestion Microservices ]
                   (Nginx / Static)            (FastAPI Replicas)        (OCR, Embeddings, RAG, KG)
                         │                           │                           │
                         │                           ▼                           ▼
                         │               ┌───────────────────────┐   ┌───────────────────────┐
                         │               │  Redis 7 Cache Layer  │   │  Background Workers   │
                         │               │ (Session, AI, Vector) │   │ (Celery / RQ / Arq)   │
                         │               └───────────┬───────────┘   └───────────┬───────────┘
                         │                           │                           │
                         └───────────────────────────┼───────────────────────────┘
                                                     ▼
                                       ┌───────────────────────────┐
                                       │   PostgreSQL 16 Cluster   │
                                       │   (Primary + Read Replica)│
                                       │  + pgvector Vector Engine │
                                       └─────────────┬─────────────┘
                                                     ▼
                                       ┌───────────────────────────┐
                                       │ Enterprise Object Storage │
                                       │   (MinIO / AWS S3 / GCS)  │
                                       └─────────────┬─────────────┘
                                                     ▼
                                       ┌───────────────────────────┐
                                       │ Monitoring & Logs Stack   │
                                       │(Prometheus, Grafana, Loki)│
                                       └───────────────────────────┘
```

---

## 3. Microservices Topology & Containerization Strategy

Every functional subsystem in KEEP runs as an isolated, containerized OCI image with non-root user execution, read-only root filesystems where applicable, and strict resource quotas:

| Service Name | Base Image | Port | Primary Responsibility | Auto-Scaling Metric |
| :--- | :--- | :--- | :--- | :--- |
| `keep-frontend` | `nginx:1.27-alpine` | 80/443 | Serves React Vite SPA bundle with gzip/brotli compression and reverse-proxy caching. | CPU > 70% or Requests > 1,000 rps |
| `keep-backend-api` | `python:3.12-slim` | 8000 | FastAPI REST & SSE Gateway; handles auth, RBAC, CRUD, and business orchestration. | CPU > 75% or Latency p95 > 250ms |
| `keep-ai-worker` | `python:3.12-slim` | 8001 | LLM inference adapter, conversational memory compaction, and prompt synthesis. | Queue Length > 20 or GPU/CPU > 80% |
| `keep-ingestion-worker`| `python:3.12-slim` | 8002 | Asynchronous document parsing, layout extraction, OCR pipelines, and chunking. | Ingestion Queue > 50 jobs |
| `keep-embedding-worker`| `python:3.12-slim` | 8003 | SentenceTransformers / Ollama dense vector embedding generation and HNSW indexing. | Embedding Batch Depth > 100 |
| `keep-notification-srv`| `python:3.12-slim` | 8004 | Multi-channel notification delivery (WebSocket, In-App, Email, Slack, Teams). | Dispatch Latency > 500ms |
| `keep-scheduler` | `python:3.12-slim` | - | Cron-based maintenance, document re-indexing, connector delta-syncs, and backup snapshots. | Fixed Singleton with Leader Election |

---

## 4. Kubernetes Orchestration & Auto-Scaling Specification

### 4.1 Pod Scheduling & Resource Quotas
Each pod definition specifies strict Kubernetes resource requests and limits to ensure deterministic multi-tenant co-existence:

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1536Mi"
```

### 4.2 Horizontal Pod Autoscaler (HPA v2)
Auto-scaling is configured per deployment targeting:
- **Min Replicas**: 2 (Ensures zero-downtime rolling updates and node-level fault tolerance)
- **Max Replicas**: 10 (Elastic capacity ceiling during high-traffic spikes)
- **Scaling Triggers**: Average CPU utilization $\ge 75\%$, Average Memory utilization $\ge 80\%$, or custom Prometheus metric `http_requests_in_flight > 150`.

### 4.3 High Availability & Pod Disruption Budgets (PDB)
- `minAvailable: 1` ensures at least one replica remains live during node drains, cordon operations, or cluster upgrades.
- Anti-affinity rules (`podAntiAffinity`) distribute identical service pods across distinct physical nodes and availability zones (`topologyKey: topology.kubernetes.io/zone`).

---

## 5. Multi-Layer Redis Caching Architecture

Caching is partitioned into discrete namespaces with custom serialization and TTL policies to prevent thundering herd problems:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Redis 7 Caching Clusters                        │
├─────────────────────┬───────────────────┬──────────────┬───────────────┤
│ Namespace           │ Key Structure     │ TTL          │ Invalidation  │
├─────────────────────┼───────────────────┼──────────────┼───────────────┤
│ `keep:session:`     │ `session:{id}`    │ 24 Hours     │ User Logout   │
│ `keep:auth:`        │ `jwt:bl:{jti}`    │ Expiry Delta │ Admin Revoke  │
│ `keep:ai:resp:`     │ `hash(prompt)`    │ 6 Hours      │ Cache Flush   │
│ `keep:vector:q:`    │ `hash(query_emb)` │ 2 Hours      │ Doc Ingestion │
│ `keep:dashboard:`   │ `org:{id}:kpis`   │ 5 Minutes    │ Mutation Hook │
│ `keep:rate_limit:`  │ `ip:{ip}:win`     │ 60 Seconds   │ Rolling Window│
└─────────────────────┴───────────────────┴──────────────┴───────────────┘
```

### Cache-Aside & Semantic Invalidation Algorithm
1. Incoming read request computes deterministic MD5/SHA256 signature of query parameters and tenant context.
2. Checks Redis:
   - **Cache Hit**: Returns cached JSON payload within $< 5\text{ms}$; increments Prometheus `cache_hits_total`.
   - **Cache Miss**: Queries PostgreSQL/pgvector; writes computed result to Redis with TTL; increments Prometheus `cache_misses_total`.
3. Entity mutation events (`document.updated`, `user.deleted`) emit event notifications that trigger wildcard key deletions or tenant-scoped namespace purges.

---

## 6. Disaster Recovery & Backup Strategy

### 6.1 Recovery Objectives
- **Recovery Point Objective (RPO)**: $\le 1\text{ hour}$ (Maximum acceptable data loss in catastrophic disaster).
- **Recovery Time Objective (RTO)**: $\le 4\text{ hours}$ (Maximum acceptable time to restore full platform operation).
- **Service Availability Target**: $\ge 99.9\%$ (Annual allowable downtime $< 8.76\text{ hours}$).

### 6.2 Backup Workflows
1. **Relational Database**: Hourly PostgreSQL continuous WAL archiving combined with daily `pg_dump` physical snapshots encrypted with AES-256.
2. **Object Storage**: Real-time cross-region replication (CRR) for uploaded documents, OCR artifacts, and audit archives.
3. **Disaster Recovery Engine**:
   - `SystemBackupService` creates point-in-time snapshots, records snapshot metadata in the `system_backups` table, computes SHA-256 integrity checksums, and monitors RPO drift.
   - Restore harness verifies snapshot unpackability and table integrity in a sandbox environment before reporting snapshot readiness.

---

## 7. Zero-Downtime Deployment & Self-Healing Strategies

### 7.1 Deployment Archetypes Supported
- **Rolling Update**: Default Kubernetes strategy replacing pods sequentially with configurable `maxSurge: 25%` and `maxUnavailable: 0%`.
- **Blue-Green Deployment**: Spawns a parallel Green environment; executes automated smoke tests; switches Ingress traffic route atomically via service selector update.
- **Canary Deployment**: Routes $5\%\to 25\%\to 50\%\to 100\%$ of incoming traffic to candidate pods while monitoring error rates via Prometheus.

### 7.2 Automated Rollback Safeguard
If deployment verification fails (HTTP 5xx rate $> 1.0\%$ or p95 latency $> 1000\text{ms}$ over 3 consecutive health checks), the orchestrator triggers an immediate automated rollback to `rollback_version` and flags the deployment as `ROLLED_BACK`.

---

## 8. Enterprise Observability & Centralized Telemetry

### 8.1 Metric Dimensions (Prometheus)
- **Infrastructure Metrics**: CPU utilization, RAM resident set size (RSS), Disk I/O, Network ingress/egress.
- **Application Performance Metrics**: Request throughput (req/s), HTTP response code distributions, p50/p90/p95/p99 latency quantiles.
- **AI Service Metrics**: Embedding generation duration, LLM token streaming velocity, OCR page throughput, RAG context synthesis duration.
- **Database Metrics**: Connection pool saturation, active queries, slow query occurrences ($> 500\text{ms}$), database storage growth.

### 8.2 Logging Architecture
Structured JSON logging outputs to `stdout` captured by fluent-bit / Promtail and shipped to Loki / Elasticsearch. Every log line includes:
`timestamp`, `level`, `service`, `trace_id`, `span_id`, `tenant_id`, `user_id`, `message`, `error_stack`.

---

## 9. System Infrastructure REST API Specifications

The infrastructure API exposes administrative controls under `/api/v1/system`:
- `GET /api/v1/system/health`: Aggregated platform and subsystem health status.
- `GET /api/v1/system/metrics`: Real-time system performance and operational KPIs.
- `GET /api/v1/system/logs`: Filtered audit and service diagnostic logs.
- `POST /api/v1/system/deploy`: Trigger managed rolling or blue-green deployment.
- `GET /api/v1/system/version`: Active platform version, git commit SHA, and environment build details.
- `GET /api/v1/system/status`: Microservices operational matrix and replica counts.
- `GET /api/v1/system/backups`: Disaster recovery snapshot inventory and RPO/RTO metrics.
- `POST /api/v1/system/backups/create`: Trigger immediate manual backup snapshot.
- `POST /api/v1/system/cache/flush`: Clear cached data across designated namespaces.


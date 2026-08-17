# Architecture Decision Log & Assumptions (docs/decisions/decisions.md)

This log records major architectural decisions (ADRs) and assumptions made during repository initialization and development.

---

## Architecture Decision Records (ADRs)

### ADR-001 — Monorepo Architecture Selection

#### Date
2026-08-17

#### Context
KEEP requires seamless co-development of frontend UI, backend FastAPI services, ingestion workers, database schemas, and devops configuration across four autonomous Antigravity development agents.

#### Decision
Establish a single monorepo structure containing `/frontend`, `/backend`, `/docker`, `/infrastructure`, `/docs`, `/tests`, and `/devdocs`.

#### Alternatives Considered
- Separate repositories for frontend and backend: Rejected due to cross-repository branch coordination complexity for autonomous agents.

#### Reason
A monorepo provides atomic Git commits across frontend and backend contract updates, simplifies CI/CD execution, and maintains a unified source of truth.

#### Impact
Agents operate on isolated feature branches within the single repository.

#### Status
ACCEPTED

---

### ADR-002 — Backend Framework & Persistence Alignment

#### Date
2026-08-17

#### Context
`devdocs/` specifies high-concurrency API performance, asynchronous background ingestion, and Python AI/ML library integration (LangChain, PyMuPDF, SentenceTransformers).

#### Decision
Adopt **FastAPI** (Python 3.12+) as the core backend API engine, combined with **SQLAlchemy 2.0 ORM**, **Alembic** migrations, and **PostgreSQL 16**.

#### Alternatives Considered
- Django REST Framework: Rejected due to synchronous ORM overhead for async AI streaming.
- Node.js Express: Rejected due to python-native AI/ML ecosystem requirements.

#### Reason
FastAPI provides native `asyncio` performance, automatic Pydantic OpenAPI schema generation, and seamless integration with Python AI packages.

#### Status
ACCEPTED

---

### ADR-003 — Multi-Tenant Isolation Pattern

#### Date
2026-08-17

#### Context
KEEP is an enterprise platform serving multiple organizations. Strict tenant data segregation is required across relational data, documents, and vector embeddings.

#### Decision
Enforce tenant isolation via an explicit `organization_id` foreign key column on all database entities and vector payload metadata.

#### Alternatives Considered
- Separate PostgreSQL schema per tenant: Rejected due to high migration and connection pool overhead for many tenants.

#### Reason
Row-level tenant filtering backed by mandatory middleware checks ensures security while maintaining operational simplicity.

#### Status
ACCEPTED

---

## Documented Assumptions

### Assumption 001 — Knowledge Graph MVP Storage Engine

#### Reason
Phase 2.4 specifies Knowledge Graph construction. Section 2.4 notes: "Future implementations may use Neo4j or Amazon Neptune, while the MVP may initially model relationships using PostgreSQL before migrating to a dedicated graph database."

#### Temporary Decision
Initial Phase 2.4 Knowledge Graph development will model entities (`kg_entities`) and relationships (`kg_relationships`) within PostgreSQL using relational tables and CTE graph queries before introducing a dedicated Neo4j service in Phase 3.6.

#### Impact
Simplifies Phase 2 infrastructure overhead while preserving full graph semantics.

#### Requires Confirmation
YES (From Human Maintainer prior to Phase 2.4)

---

### Assumption 002 — Vector Store Selection for Local Development

#### Reason
`devdocs/` Phase 2.1 & 2.2 specify vector embedding storage and retrieval without forcing a single vector vendor for local dev vs production.

#### Temporary Decision
Use PostgreSQL with `pgvector` extension for standard local Docker Compose development to minimize container count, with an abstract vector repository layer allowing seamless pluggability for Qdrant / Chroma in production.

#### Impact
Reduces system resource usage during local four-agent test execution.

#### Requires Confirmation
NO (Implementation detail abstracted via vector service layer)

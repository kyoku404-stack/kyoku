# KEEP Enterprise Platform

Feature-oriented monorepo layout separating application concerns while keeping shared documentation and infrastructure manifests unified.

---

## 📁 Monorepo Directory Layout

```
keep/
├── frontend/             # Next.js / React Web App
├── backend/              # FastAPI Server & AI Services
├── infrastructure/       # Terraform & Kubernetes manifests
├── docker/               # Dockerfiles & compose files
├── docs/                 # Platform specifications & SRS
├── scripts/              # Dev setup & database seeds
├── tests/                # E2E integration test suite
├── .github/              # CI/CD action workflows
├── docker-compose.yml    # Local multi-container mesh
└── README.md             # Developer Onboarding Guide
```

---

## 🎨 Frontend Feature Organization (`frontend/src/`)

```
frontend/src/
├── app/                  # Routing & Core App Shell
├── features/             # Modular Domain Features
│   ├── auth/             # Authentication & SSO
│   ├── dashboard/        # Executive Analytics
│   ├── search/           # Hybrid Vector/Graph Search
│   ├── upload/           # Document Ingestion UI
│   └── chat/             # Graph RAG Conversational UI
├── components/           # Shared UI Design System
├── services/             # Axios/Fetch API Clients
├── store/                # Global State Handlers
└── styles/               # CSS & Tailwind Tokens
```

---

## ⚙️ Backend Module Hierarchy (`backend/app/`)

```
backend/app/
├── api/v1/               # Versioned REST Controllers
│   ├── auth.py           # Identity Endpoints
│   ├── documents.py      # Ingestion API
│   └── chat.py           # RAG Query Stream
├── core/                 # App Settings & Security
│   ├── config.py         # Pydantic Env Validation
│   └── security.py       # Hashing & Token Logic
├── models/               # SQLAlchemy ORM Entities
├── schemas/              # Pydantic DTO Schemas
├── repositories/         # Database Access Layer
├── ai/                   # LangChain / LlamaIndex Core
└── main.py               # FastAPI App Initialization
```

---

## 📚 Documentation Hierarchy (`docs/`)

```
docs/
├── SRS/                  # Software Requirements
├── Architecture/         # C4 & Topology Specs
├── Database/             # ERD & Polyglot Specs
├── API/                  # OpenAPI / GraphQL Specs
├── UIUX/                 # Figma & Wireframes
├── Research/             # Vector & Graph Benchmarks
└── Deployment/           # AWS / K8s Deployment Specs
```

# Database Schema Specification (docs/database/database-schema.md)

> **Evolving Engineering Database Documentation for KEEP**  
> *Derived from Phase 1.3, Phase 1.4, Phase 1.5, Phase 1.8, Phase 2.1, and Phase 2.4 of `devdocs/` specifications.*

---

## 1. Relational Database Overview

KEEP uses **PostgreSQL 16** as its primary multi-tenant relational persistence layer. All models are defined using **SQLAlchemy 2.0 ORM** and schema evolution is managed via **Alembic** migrations.

---

## 2. Core Entity Schemas

### 2.1 `organizations` Table
Stores multi-tenant enterprise organization details.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Unique organization identifier |
| `name` | `VARCHAR(255)` | NOT NULL | Name of the enterprise |
| `domain` | `VARCHAR(255)` | Unique | Domain name (e.g. enterprise.com) |
| `is_active` | `BOOLEAN` | Default `TRUE` | Account status |
| `created_at` | `TIMESTAMP` | Default `NOW()` | Timestamp created |

---

### 2.2 `users` Table
Stores user credentials, profile information, and tenant mapping.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Unique user identifier |
| `organization_id` | `UUID` | FK -> `organizations.id` | Multi-tenant tenant boundary |
| `email` | `VARCHAR(255)` | NOT NULL, Unique | User login email |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | Bcrypt hashed password |
| `full_name` | `VARCHAR(255)` | NOT NULL | User full name |
| `role` | `VARCHAR(50)` | NOT NULL, Default `'Member'` | RBAC role (`SuperAdmin`, `OrgAdmin`, `Manager`, `Member`, `Guest`) |
| `is_active` | `BOOLEAN` | Default `TRUE` | Active status |
| `created_at` | `TIMESTAMP` | Default `NOW()` | Registration timestamp |

---

### 2.3 `documents` Table
Tracks uploaded files and processing metadata.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Unique document identifier |
| `organization_id` | `UUID` | FK -> `organizations.id` | Multi-tenant tenant boundary |
| `uploader_id` | `UUID` | FK -> `users.id` | User who uploaded file |
| `filename` | `VARCHAR(255)` | NOT NULL | Original filename |
| `file_path` | `TEXT` | NOT NULL | Storage path / URI |
| `file_type` | `VARCHAR(50)` | NOT NULL | MIME type / Extension (PDF, DOCX, etc.) |
| `file_size` | `BIGINT` | NOT NULL | Size in bytes |
| `status` | `VARCHAR(50)` | Default `'PENDING'` | Status (`PENDING`, `PROCESSING`, `PROCESSED`, `FAILED`) |
| `created_at` | `TIMESTAMP` | Default `NOW()` | Upload timestamp |

---

### 2.4 `document_chunks` Table (Vector / Ingestion Layer)
Stores text chunks, vector embeddings, and chunk-level metadata.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Chunk identifier |
| `document_id` | `UUID` | FK -> `documents.id` | Parent document |
| `chunk_index` | `INT` | NOT NULL | Sequential chunk index |
| `content` | `TEXT` | NOT NULL | Extracted text chunk |
| `embedding` | `vector(1536)` | Index (HNSW / IVFFlat) | High-dimensional embedding vector |
| `metadata_json` | `JSONB` | Default `{}` | Page number, section title, OCR confidence |

---

### 2.5 `kg_entities` & `kg_relationships` Tables (Knowledge Graph MVP)
Models semantic enterprise entities and interconnections.

- **`kg_entities`**: `id`, `organization_id`, `name`, `entity_type` (Person, Project, Document, Department, Policy), `properties_json`.
- **`kg_relationships`**: `id`, `organization_id`, `source_entity_id`, `target_entity_id`, `relation_type` (AUTHOR_OF, ASSIGNED_TO, BELONGS_TO, DEPENDS_ON), `weight`.

---

## 3. Database Migration Strategy

1. All schema modifications MUST be executed via Alembic migrations.
2. Migration files reside in `/backend/app/db/migrations/versions/`.
3. To generate a migration:
   ```bash
   alembic revision --autogenerate -m "description of schema change"
   ```
4. To apply migrations:
   ```bash
   alembic upgrade head
   ```

---

## 4. Database Ownership

- **Primary Owner**: Agent 3 (Database / Data / Ingestion)
- **Secondary Owner**: Agent 1 (Backend API)

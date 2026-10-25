# Database Schema Specification (docs/database/database-schema.md)

> **Official Engineering Database & Persistence Layer Specification for KEEP**  
> *Approved by: Member 1 (Project Lead & AI Architect)*  
> *Target Implementer: Member 2 (Backend Lead) | Consumer: Member 3 (Frontend Lead) | Ops: Member 4 (DevOps Lead)*  
> *Derived from: devdocs/p1/p1.3.txt (Chapters 1–22)*

---

## 1. Relational Database Overview & Technology Stack

KEEP uses **PostgreSQL 16** enhanced with the **pgvector** extension as its unified multi-tenant relational persistence and vector similarity store. All application models are defined using **SQLAlchemy 2.0 ORM** (fully typed, async-first via `asyncpg`), and schema migrations are tracked and applied via **Alembic**.

### 1.1 Technology Matrix
| Layer / Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Relational Database** | PostgreSQL | 16 Alpine | Primary multi-tenant relational data store |
| **Vector Search Extension** | pgvector | 0.7+ | 1536-dim / 384-dim dense embedding index (HNSW / IVFFlat) |
| **ORM & Query Builder** | SQLAlchemy | 2.0+ (Async) | Typed models, session lifecycle, Unit of Work |
| **Database Driver** | asyncpg / psycopg2 | latest | High-performance asynchronous PostgreSQL driver |
| **Schema Migrations** | Alembic | latest | Version-controlled, reproducible schema revisions |
| **Data Validation** | Pydantic v2 | 2.8+ | Ingestion DTO validation & serialization |

---

## 2. Global Model Mixins & Standards

All database tables in KEEP conform to strict enterprise standards:
1. **UUID Primary Keys**: Every table uses a RFC 4122 compliant UUID primary key generated via `uuid.uuid4()` / `gen_random_uuid()`.
2. **Audit Timestamps (`TimestampMixin`)**: Every record tracks `created_at` (UTC timestamp) and `updated_at` (UTC timestamp automatically updated on change).
3. **Soft Deletion (`SoftDeleteMixin`)**: Critical entities implement `is_deleted` (boolean, default `FALSE`) and `deleted_at` (timestamp, default `NULL`).
4. **Tenant Segregation (`TenantMixin`)**: All tenant-scoped tables enforce a foreign key `organization_id` referencing `organizations(id)` with `ON DELETE CASCADE`.

---

## 3. Entity Schemas & Tables

### 3.1 `organizations` Table
Root container for enterprise multi-tenancy.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique organization identifier |
| `name` | `VARCHAR(255)` | NOT NULL | Enterprise display name |
| `domain` | `VARCHAR(255)` | NOT NULL, Unique | Organization primary domain (e.g. `enterprise.com`) |
| `subscription_tier` | `VARCHAR(50)` | NOT NULL, Default `'Enterprise'` | Billing / SLA tier (`Free`, `Pro`, `Enterprise`) |
| `max_users` | `INT` | NOT NULL, Default `1000` | User seat quota |
| `max_storage_bytes` | `BIGINT` | NOT NULL, Default `107374182400` | Storage quota (default 100 GB) |
| `ai_monthly_token_quota` | `BIGINT` | NOT NULL, Default `10000000` | Monthly LLM token quota |
| `is_active` | `BOOLEAN` | NOT NULL, Default `TRUE` | Tenant operational status |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Registration timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.2 `users` Table
Stores enterprise user credentials, profile information, and role assignments.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique user identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary foreign key |
| `email` | `VARCHAR(255)` | NOT NULL | User login email |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | Bcrypt / Argon2 hashed password |
| `full_name` | `VARCHAR(255)` | NOT NULL | User full legal/display name |
| `role` | `VARCHAR(50)` | NOT NULL, Default `'Member'` | RBAC role (`SuperAdmin`, `OrgAdmin`, `Manager`, `Member`, `Guest`) |
| `avatar_url` | `VARCHAR(512)` | NULL | Optional profile avatar image URL |
| `is_active` | `BOOLEAN` | NOT NULL, Default `TRUE` | User account active status |
| `is_verified` | `BOOLEAN` | NOT NULL, Default `FALSE` | Email verification flag |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Registration timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

**Table Constraints**:
- `CONSTRAINT uq_users_org_email UNIQUE (organization_id, email)`

---

### 3.3 `departments` Table (Phase 1.5 Hierarchy)
Functional business units grouping teams, projects, and organizational domains.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique department identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary foreign key |
| `name` | `VARCHAR(255)` | NOT NULL | Department name (e.g. `Engineering`, `Human Resources`) |
| `description` | `TEXT` | NULL | Department mission charter |
| `manager_id` | `UUID` | NULL, FK -> `users.id` | Department head / manager |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

**Table Constraints**:
- `CONSTRAINT uq_departments_org_name UNIQUE (organization_id, name)`

---

### 3.4 `invitations` Table (Phase 1.5 User Onboarding)
Tracks pending, accepted, and revoked enterprise member invitations.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique invitation identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary foreign key |
| `department_id` | `UUID` | NULL, FK -> `departments.id` ON DELETE SET NULL | Pre-assigned department |
| `team_id` | `UUID` | NULL, FK -> `teams.id` ON DELETE SET NULL | Pre-assigned team |
| `email` | `VARCHAR(255)` | NOT NULL | Invitee destination email |
| `role` | `VARCHAR(50)` | NOT NULL, Default `'Member'` | Pre-assigned role (`OrgAdmin`, `ProjectManager`, `Member`, `Viewer`) |
| `token` | `VARCHAR(255)` | NOT NULL, Unique | Secure one-time onboarding token |
| `status` | `VARCHAR(50)` | NOT NULL, Default `'PENDING'` | Invitation status (`PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED`) |
| `invited_by_id` | `UUID` | NOT NULL, FK -> `users.id` | Inviting admin or manager |
| `expires_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | Token expiration timestamp (default 7 days) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Invitation dispatch timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last status update |

**Table Constraints**:
- `CONSTRAINT uq_invitations_org_email_pending UNIQUE (organization_id, email, status)`

---

### 3.5 `teams` & `team_members` Tables
Models departmental divisions and collaborative workspaces.

#### `teams` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique team identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary foreign key |
| `department_id` | `UUID` | NULL, FK -> `departments.id` ON DELETE SET NULL | Parent department (Phase 1.5 hierarchy) |
| `name` | `VARCHAR(255)` | NOT NULL | Department / Team name (e.g. `Backend Team`) |
| `description` | `TEXT` | NULL | Team charter or description |
| `lead_user_id` | `UUID` | NULL, FK -> `users.id` | Assigned team lead |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

**Table Constraints**:
- `CONSTRAINT uq_teams_org_name UNIQUE (organization_id, name)`

#### `team_members` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `team_id` | `UUID` | NOT NULL, FK -> `teams.id` ON DELETE CASCADE | Parent team |
| `user_id` | `UUID` | NOT NULL, FK -> `users.id` ON DELETE CASCADE | Member user |
| `role_in_team` | `VARCHAR(50)` | NOT NULL, Default `'Member'` | Team-level role (`Lead`, `Member`, `Observer`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Join timestamp |

**Table Constraints**:
- `PRIMARY KEY (team_id, user_id)`

---

### 3.4 `projects` Table
Enterprise initiatives, workspaces, and knowledge groupings.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique project identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary foreign key |
| `team_id` | `UUID` | NULL, FK -> `teams.id` | Associated team |
| `owner_id` | `UUID` | NOT NULL, FK -> `users.id` | Project creator / owner |
| `name` | `VARCHAR(255)` | NOT NULL | Project name |
| `description` | `TEXT` | NULL | Project scope and details |
| `status` | `VARCHAR(50)` | NOT NULL, Default `'ACTIVE'` | Status (`ACTIVE`, `ARCHIVED`, `COMPLETED`) |
| `priority` | `VARCHAR(50)` | NOT NULL, Default `'MEDIUM'` | Priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.5 `documents` Table
Represents logical digital knowledge assets, metadata headers, and container references for document version lineage.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique document identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary foreign key |
| `uploader_id` | `UUID` | NOT NULL, FK -> `users.id` | User who uploaded the file |
| `project_id` | `UUID` | NULL, FK -> `projects.id` ON DELETE SET NULL | Associated project container |
| `current_version_id`| `UUID` | NULL, FK -> `document_versions.id` ON DELETE SET NULL | Pointer to active document version snapshot |
| `current_version_number`| `INT` | NOT NULL, Default `1` | Latest sequential version number |
| `filename` | `VARCHAR(255)` | NOT NULL | Sanitized storage filename |
| `original_filename`| `VARCHAR(255)` | NOT NULL | Original user filename at upload |
| `title` | `VARCHAR(255)` | NULL | User-specified display title |
| `description` | `TEXT` | NULL | Document description / abstract |
| `file_path` | `TEXT` | NOT NULL | Storage path (`storage/{org_id}/documents/{doc_id}/v{ver}/{filename}`) |
| `file_type` | `VARCHAR(50)` | NOT NULL | Normalized extension (`pdf`, `docx`, `txt`, `png`) |
| `mime_type` | `VARCHAR(100)` | NOT NULL | Canonical MIME type (e.g. `application/pdf`) |
| `file_size` | `BIGINT` | NOT NULL | File size in bytes |
| `checksum_sha256` | `VARCHAR(64)` | NOT NULL | SHA-256 cryptographic digest for integrity & deduplication |
| `category` | `VARCHAR(50)` | NOT NULL, Default `'REPORTS'` | Category (`POLICIES`, `REPORTS`, `MEETING_MINUTES`, `RESEARCH`, `LEGAL`, `FINANCE`, `HR`, `TECHNICAL_DOCUMENTATION`, `PRESENTATIONS`, `TRAINING_MATERIALS`) |
| `tags` | `JSONB` | NOT NULL, Default `'[]'::jsonb` | Categorization tags array |
| `status` | `VARCHAR(50)` | NOT NULL, Default `'AWAITING_PROCESSING'` | State (`PENDING`, `VALIDATED`, `AWAITING_PROCESSING`, `QUEUED`, `EXTRACTING`, `CHUNKING`, `EMBEDDING`, `READY_FOR_AI`, `FAILED`, `ARCHIVED`) |
| `chunk_count` | `INT` | NOT NULL, Default `0` | Number of generated chunks in pgvector |
| `error_message` | `TEXT` | NULL | Parsing or vectorization failure details |
| `metadata_json` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Extracted attributes (page_count, author, word_count, language, ocr_applied) |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Upload timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.5.1 `document_versions` Table (Phase 1.8 Versioning & Lineage)
Stores immutable physical file revisions, author attributions, change notes, and version snapshots for audit and rollback.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique version snapshot identifier |
| `document_id` | `UUID` | NOT NULL, FK -> `documents.id` ON DELETE CASCADE | Parent document reference |
| `version_number` | `INT` | NOT NULL | Sequential version index ($1, 2, 3, \dots$) |
| `file_path` | `TEXT` | NOT NULL | Physical storage path on disk or cloud bucket |
| `file_size` | `BIGINT` | NOT NULL | Revision file size in bytes |
| `checksum_sha256` | `VARCHAR(64)` | NOT NULL | SHA-256 digest of this version's binary stream |
| `mime_type` | `VARCHAR(100)` | NOT NULL | MIME type of this version's content |
| `uploader_id` | `UUID` | NOT NULL, FK -> `users.id` | User who authored or uploaded this revision |
| `change_notes` | `TEXT` | NULL | User-provided summary of modifications |
| `metadata_json` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Version-specific extraction metadata |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Revision creation timestamp |

**Table Constraints**:
- `CONSTRAINT uq_doc_versions_doc_num UNIQUE (document_id, version_number)`

---

### 3.6 `document_chunks` Table (Vector Persistence Layer)
Stores text chunks, vector embeddings, and chunk metadata for Hybrid RAG.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique chunk identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Multi-tenant boundary |
| `document_id` | `UUID` | NOT NULL, FK -> `documents.id` ON DELETE CASCADE | Parent document reference |
| `document_version_id`| `UUID`| NULL, FK -> `document_versions.id` ON DELETE CASCADE | Provenanced version snapshot reference (Phase 1.8) |
| `chunk_index` | `INT` | NOT NULL | Sequential chunk index within document |
| `content` | `TEXT` | NOT NULL | Raw chunk text content |
| `token_count` | `INT` | NOT NULL, Default `0` | Estimated token count |
| `page_number` | `INT` | NULL | Provenanced page number in source document |
| `section_title` | `VARCHAR(255)` | NULL | Heading / Section title |
| `embedding` | `vector(1536)` | NULL | Vector embedding (OpenAI / HuggingFace) |
| `metadata_json` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Additional chunk metadata (e.g. bounding boxes) |
| `tsv_content` | `tsvector` | GENERATED STORED | Full-text search vector for lexical BM25 matching |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

**Table Constraints**:
- `CONSTRAINT uq_chunks_doc_idx UNIQUE (document_id, chunk_index)`

---

### 3.7 `kg_entities` & `kg_relationships` Tables (Knowledge Graph MVP)
Models interconnected enterprise semantic entities and relations in PostgreSQL.

#### `kg_entities` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique entity identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary |
| `name` | `VARCHAR(255)` | NOT NULL | Normalized entity name |
| `entity_type` | `VARCHAR(100)` | NOT NULL | Entity type (`Person`, `Project`, `Technology`, `Department`, `Document`) |
| `description` | `TEXT` | NULL | Semantic description |
| `source_document_id`| `UUID` | NULL, FK -> `documents.id` ON DELETE SET NULL | Origin document if extracted by AI |
| `properties` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Arbitrary key-value properties |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

**Table Constraints**:
- `CONSTRAINT uq_kg_entity_org_name_type UNIQUE (organization_id, name, entity_type)`

#### `kg_relationships` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique relationship edge identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary |
| `source_entity_id` | `UUID` | NOT NULL, FK -> `kg_entities.id` ON DELETE CASCADE | Origin entity |
| `target_entity_id` | `UUID` | NOT NULL, FK -> `kg_entities.id` ON DELETE CASCADE | Target entity |
| `relation_type` | `VARCHAR(100)` | NOT NULL | Directed relation (`AUTHOR_OF`, `ASSIGNED_TO`, `DEPENDS_ON`, `BELONGS_TO`) |
| `weight` | `FLOAT` | NOT NULL, Default `1.0` | Edge strength / frequency |
| `confidence_score`| `FLOAT` | NOT NULL, Default `1.0` | AI extraction confidence (0.0 to 1.0) |
| `source_document_id`| `UUID` | NULL, FK -> `documents.id` ON DELETE SET NULL | Origin document |
| `properties` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Edge metadata |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.8 `meetings` & `tasks` Tables

#### `meetings` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique meeting identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary |
| `project_id` | `UUID` | NULL, FK -> `projects.id` | Related project |
| `organizer_id` | `UUID` | NOT NULL, FK -> `users.id` | Meeting organizer |
| `title` | `VARCHAR(255)` | NOT NULL | Meeting title |
| `scheduled_start` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | Start time |
| `scheduled_end` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | End time |
| `recording_url` | `VARCHAR(512)` | NULL | Optional recording link |
| `transcript_text`| `TEXT` | NULL | Raw or processed transcript text |
| `summary_text` | `TEXT` | NULL | AI-generated summary |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

#### `tasks` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique task identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary |
| `project_id` | `UUID` | NULL, FK -> `projects.id` | Related project |
| `creator_id` | `UUID` | NOT NULL, FK -> `users.id` | Task creator |
| `assignee_id` | `UUID` | NULL, FK -> `users.id` | Assigned user |
| `title` | `VARCHAR(255)` | NOT NULL | Task title |
| `description` | `TEXT` | NULL | Task details |
| `priority` | `VARCHAR(50)` | NOT NULL, Default `'MEDIUM'` | Priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `status` | `VARCHAR(50)` | NOT NULL, Default `'TODO'` | Status (`TODO`, `IN_PROGRESS`, `DONE`, `CANCELLED`) |
| `due_date` | `TIMESTAMP WITH TIME ZONE` | NULL | Due date |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.9 `chat_sessions`, `chat_messages` & `ai_feedback` Tables

#### `chat_sessions` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique conversation session ID |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary |
| `user_id` | `UUID` | NOT NULL, FK -> `users.id` | User owner |
| `project_id` | `UUID` | NULL, FK -> `projects.id` | Optional project context filter |
| `title` | `VARCHAR(255)` | NOT NULL, Default `'New Conversation'` | Session topic |
| `is_archived` | `BOOLEAN` | NOT NULL, Default `FALSE` | Archived state |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

#### `chat_messages` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique message ID |
| `session_id` | `UUID` | NOT NULL, FK -> `chat_sessions.id` ON DELETE CASCADE | Parent conversation session |
| `role` | `VARCHAR(50)` | NOT NULL | Message role (`user`, `assistant`, `system`, `tool`) |
| `content` | `TEXT` | NOT NULL | Message text |
| `model_name` | `VARCHAR(100)` | NULL | AI model used (e.g. `gpt-4o`) |
| `tokens_prompt` | `INT` | NOT NULL, Default `0` | Prompt token count |
| `tokens_completion`| `INT` | NOT NULL, Default `0` | Completion token count |
| `latency_ms` | `FLOAT` | NOT NULL, Default `0.0` | Response generation latency |
| `citations_json` | `JSONB` | NOT NULL, Default `'[]'::jsonb` | Provenanced citations array |
| `tool_calls_json` | `JSONB` | NOT NULL, Default `'[]'::jsonb` | Tool invocations & arguments |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Timestamp |

#### `ai_feedback` Table:
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Feedback ID |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary |
| `user_id` | `UUID` | NOT NULL, FK -> `users.id` | Feedback author |
| `message_id` | `UUID` | NOT NULL, FK -> `chat_messages.id` ON DELETE CASCADE | Evaluated AI message |
| `rating` | `INT` | NOT NULL | Rating (`1` for positive, `-1` for negative) |
| `comment` | `TEXT` | NULL | Optional text explanation |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Timestamp |

---

### 3.10 `activity_logs` Table (Audit Trail)
Immutable security and audit event logging. Captures authentication, workspace operations, and all Phase 1.6 authorization verdicts (`PERMISSION_GRANTED` and `PERMISSION_DENIED`).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique audit event identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary |
| `user_id` | `UUID` | NULL, FK -> `users.id` | Actor user ID (NULL for system events) |
| `action` | `VARCHAR(100)` | NOT NULL | Action name (e.g. `USER_LOGIN`, `PERMISSION_GRANTED`, `PERMISSION_DENIED`, `DOCUMENT_UPLOAD`, `AI_QUERY`) |
| `resource_type` | `VARCHAR(100)` | NOT NULL | Target entity type (`document`, `project`, `meeting`, `organization`, `chat_session`, `user`) |
| `resource_id` | `VARCHAR(255)` | NULL | Target entity UUID string |
| `ip_address` | `VARCHAR(45)` | NULL | Client IP address |
| `user_agent` | `VARCHAR(512)` | NULL | Client user agent string |
| `metadata_json` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Detailed event payload (e.g. `{"required_permission": "document.delete", "decision": "ALLOW", "error_code": null, "reason": "owner_override"}`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Event timestamp |

---

### 3.11 `notifications` Table (Phase 1.7 Dashboard & User Experience)
Stores user-directed notifications with status tracking, categorization, action links, and soft-delete capabilities.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique notification identifier |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` ON DELETE CASCADE | Tenant boundary foreign key |
| `user_id` | `UUID` | NOT NULL, FK -> `users.id` ON DELETE CASCADE | Recipient user identifier |
| `type` | `VARCHAR(50)` | NOT NULL, Default `'info'` | Category (`info`, `warning`, `success`, `error`, `reminder`) |
| `title` | `VARCHAR(255)` | NOT NULL | Short notification title |
| `body` | `TEXT` | NOT NULL | Detailed notification body message |
| `action_url` | `VARCHAR(512)` | NULL | Optional deep-link destination URL |
| `is_read` | `BOOLEAN` | NOT NULL, Default `FALSE` | Read receipt flag |
| `is_deleted` | `BOOLEAN` | NOT NULL, Default `FALSE` | Soft delete flag |
| `deleted_at` | `TIMESTAMP WITH TIME ZONE` | NULL | Soft delete timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Last modification timestamp |

---

### 3.12 System Observability, Request Tracing & AI Telemetry Schemas

To support distributed tracing, structured audit querying, and Phase 2 AI observability, operational records are linked with correlation identifiers.

#### `activity_logs` Observability Metadata Schema
The `metadata_json` JSONB column in `activity_logs` is formally standardized to capture distributed tracing and latency context across all recorded audit operations:

```json
{
  "request_id": "req-98f24a1b-312c-47ea-8d19-bca128f73110",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "execution_time_ms": 14.82,
  "module": "authorization_engine",
  "decision": "ALLOW",
  "required_permission": "document.read",
  "actor_role": "Member",
  "details": {
    "document_id": "e8b23f11-9a1c-4b62-9e22-83bfa99321e1"
  }
}
```

#### `ai_telemetry_logs` Specification (Phase 2 Ingestion & RAG Foundation)
For high-volume AI telemetry (LLM calls, embeddings, vector retrieval evaluations), operational events in Phase 2 are structured with the following schema:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default `gen_random_uuid()` | Unique AI telemetry event ID |
| `organization_id` | `UUID` | NOT NULL, FK -> `organizations.id` | Tenant boundary for AI cost attribution |
| `user_id` | `UUID` | NULL, FK -> `users.id` | Invoking user |
| `project_id` | `UUID` | NULL, FK -> `projects.id` | Associated workspace container |
| `operation_type` | `VARCHAR(50)` | NOT NULL | `EMBEDDING_GENERATION`, `VECTOR_SEARCH`, `LLM_COMPLETION`, `RAG_QUERY` |
| `model_name` | `VARCHAR(100)` | NOT NULL | Model identifier (e.g., `gpt-4o`, `text-embedding-3-small`) |
| `prompt_tokens` | `INT` | NOT NULL, Default `0` | Number of prompt tokens |
| `completion_tokens` | `INT` | NOT NULL, Default `0` | Number of completion tokens |
| `total_tokens` | `INT` | NOT NULL, Default `0` | Sum of prompt and completion tokens |
| `latency_ms` | `FLOAT` | NOT NULL, Default `0.0` | Total operation latency in milliseconds |
| `cost_usd` | `NUMERIC(10, 6)` | NOT NULL, Default `0.000000` | Estimated financial cost in USD |
| `trace_id` | `VARCHAR(64)` | NULL | W3C trace identifier |
| `request_id` | `VARCHAR(64)` | NULL | Request correlation identifier |
| `metrics_json` | `JSONB` | NOT NULL, Default `'{}'::jsonb` | Additional telemetry (TTFT, similarity scores, candidate count) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, Default `NOW()` | Event timestamp |

---

## 4. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    ORGANIZATION ||--o{ DEPARTMENT : "divides_into"
    ORGANIZATION ||--o{ INVITATION : "issues"
    ORGANIZATION ||--o{ USER : "has"
    ORGANIZATION ||--o{ TEAM : "has"
    ORGANIZATION ||--o{ PROJECT : "contains"
    ORGANIZATION ||--o{ DOCUMENT : "owns"
    ORGANIZATION ||--o{ KG_ENTITY : "scopes"
    ORGANIZATION ||--o{ CHAT_SESSION : "scopes"
    ORGANIZATION ||--o{ ACTIVITY_LOG : "records"

    DEPARTMENT ||--o{ TEAM : "contains"
    DEPARTMENT ||--o{ INVITATION : "assigns"

    TEAM ||--o{ TEAM_MEMBER : "includes"
    TEAM ||--o{ PROJECT : "executes"
    USER ||--o{ TEAM_MEMBER : "belongs_to"

    PROJECT ||--o{ DOCUMENT : "groups"
    PROJECT ||--o{ MEETING : "schedules"
    PROJECT ||--o{ TASK : "tracks"

    DOCUMENT ||--o{ DOCUMENT_VERSION : "tracks_versions"
    DOCUMENT_VERSION ||--o{ DOCUMENT_CHUNK : "chunks_into"
    DOCUMENT ||--o{ KG_ENTITY : "extracted_from"

    KG_ENTITY ||--o{ KG_RELATIONSHIP : "source_of"
    KG_ENTITY ||--o{ KG_RELATIONSHIP : "target_of"

    USER ||--o{ CHAT_SESSION : "conducts"
    USER ||--o{ NOTIFICATION : "receives"
    ORGANIZATION ||--o{ NOTIFICATION : "scopes"
    CHAT_SESSION ||--o{ CHAT_MESSAGE : "contains"
    CHAT_MESSAGE ||--o{ AI_FEEDBACK : "evaluated_by"
```

---

## 5. Indexing Matrix

| Table | Index Name | Index Method | Target Columns | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `departments` | `idx_depts_org_name` | B-tree (Unique) | `organization_id, name` | Tenant department uniqueness |
| `invitations` | `idx_invites_org_email` | B-tree | `organization_id, email, status` | Invitation token and status lookups |
| `invitations` | `idx_invites_token` | B-tree (Unique) | `token` | Rapid invitation redemption |
| `teams` | `idx_teams_dept` | B-tree | `organization_id, department_id` | Departmental team filtering |
| `users` | `idx_users_org_email` | B-tree (Unique) | `organization_id, email` | Multi-tenant auth lookup |
| `documents` | `idx_docs_org_status` | B-tree | `organization_id, status, created_at` | Ingestion status filtering |
| `documents` | `idx_docs_org_checksum` | B-tree | `organization_id, checksum_sha256` | Multi-tenant duplicate document detection |
| `documents` | `idx_docs_category` | B-tree | `organization_id, category` | Category-based document browsing & filtering |
| `documents` | `idx_docs_project` | B-tree | `organization_id, project_id` | Project workspace containment & permissions |
| `document_versions` | `idx_doc_versions_doc_ver` | B-tree (Unique) | `document_id, version_number` | Rapid version retrieval & lineage ordering |
| `document_versions` | `idx_doc_versions_checksum` | B-tree | `checksum_sha256` | Version file integrity & global dedup check |
| `document_chunks` | `idx_chunks_embedding_hnsw` | HNSW | `embedding (vector_cosine_ops)` | High-speed vector similarity |
| `document_chunks` | `idx_chunks_tsv` | GIN | `tsv_content` | BM25 lexical full-text search |
| `document_chunks` | `idx_chunks_org_doc` | B-tree | `organization_id, document_id` | Tenant chunk retrieval |
| `document_chunks` | `idx_chunks_doc_version` | B-tree | `document_version_id` | Version-scoped chunk activation & pruning |
| `kg_entities` | `idx_kg_entities_org_type` | B-tree | `organization_id, entity_type` | Semantic entity lookups |
| `kg_relationships` | `idx_kg_rel_src` | B-tree | `organization_id, source_entity_id` | Forward graph traversals |
| `kg_relationships` | `idx_kg_rel_tgt` | B-tree | `organization_id, target_entity_id` | Reverse graph traversals |
| `chat_messages` | `idx_chat_msg_session` | B-tree | `session_id, created_at ASC` | Chronological chat history |
| `activity_logs` | `idx_activity_org_date` | B-tree | `organization_id, created_at DESC` | Security audit queries |
| `notifications` | `ix_notifications_user_unread` | B-tree | `user_id, is_read` | High-frequency unread notifications lookup |
| `notifications` | `ix_notifications_org_created` | B-tree | `organization_id, created_at DESC` | Organization-scoped chronological feed |

---

## 6. Migration Strategy & Versioning

1. All database migrations are managed using **Alembic** under `backend/migrations/versions/`.
2. Migration filenames follow the convention: `<revision_id>_<phase>_<slug>.py` (e.g. `001_p1_3_core_persistence_schema.py`).
3. Migrations must implement both `upgrade()` and `downgrade()` methods cleanly.
4. Auto-generation commands:
   ```bash
   alembic revision --autogenerate -m "feat(phase-1.3): implement core persistence layer and vector models"
   ```
5. Applying migrations:
   ```bash
   alembic upgrade head
   ```

---

## 7. Domain Ownership

- **Architecture & AI Validation Lead**: Member 1 (Project Lead & AI Architect)
- **Primary Code Owner & Implementation**: Member 2 (Backend & Database Lead)
- **Frontend Alignment**: Member 3 (Frontend Lead)
- **Containerization & CI Validation**: Member 4 (DevOps & Integration Lead)

---

### 3.13 Ingestion Jobs & Background Pipeline Schema (`ingestion_jobs`) — Phase 2.1 Specification

To track the ten-stage asynchronous document ingestion pipeline, Phase 2.1 establishes the `ingestion_jobs` relational model, tracking progress, chunking statistics, OCR invocation, and failure diagnostics:

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    current_stage VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress_percent FLOAT NOT NULL DEFAULT 0.0,
    total_pages INTEGER NOT NULL DEFAULT 0,
    processed_pages INTEGER NOT NULL DEFAULT 0,
    chunks_generated INTEGER NOT NULL DEFAULT 0,
    embeddings_generated INTEGER NOT NULL DEFAULT 0,
    ocr_applied BOOLEAN NOT NULL DEFAULT FALSE,
    chunking_strategy VARCHAR(50) NOT NULL DEFAULT 'SEMANTIC_HEADING_AWARE',
    embedding_provider VARCHAR(50) NOT NULL DEFAULT 'OPENAI',
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    error_details_json JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ingestion_job_status CHECK (
        status IN ('PENDING', 'EXTRACTING', 'OCR_PROCESSING', 'NORMALIZING', 
                   'CHUNKING', 'EMBEDDING', 'INDEXING', 'COMPLETED', 'FAILED', 'RETRYING')
    )
);

-- Composite & Performance Indexes
CREATE INDEX idx_ingestion_jobs_tenant_status ON ingestion_jobs(organization_id, status);
CREATE INDEX idx_ingestion_jobs_document ON ingestion_jobs(document_id, document_version_id);
CREATE INDEX idx_ingestion_jobs_created_at ON ingestion_jobs(created_at DESC);
```

#### Enhanced Metadata Mapping in `document_chunks`
During Phase 2.1 ingestion, generated chunks are persisted into `document_chunks` with enhanced metadata in `metadata_json`:
- `section_title`: Heading title extracted from the document hierarchy.
- `page_number`: 1-indexed document page where chunk originates.
- `token_count`: Accurate BPE token length.
- `character_count`: String character count.
- `checksum_sha256`: Cryptographic hash of the chunk text for deduplication.

---

### 3.14 Phase 2.2 — RAG Queries, Citations & Feedback Schema

#### 3.14.1 Full-Text Search Vector on `document_chunks`
To support Hybrid Sparse Retrieval alongside dense vector embeddings, `document_chunks` incorporates full-text search capabilities:
```sql
-- Generated tsvector column for English lexical indexing
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;

-- GIN index for high-speed keyword matching
CREATE INDEX IF NOT EXISTS idx_document_chunks_search_vector ON document_chunks USING gin(search_vector);
```

#### 3.14.2 `rag_queries` Table
Logs all enterprise RAG interactions, tokens, latency, and grounded responses:
```sql
CREATE TABLE rag_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    normalized_query TEXT,
    response_text TEXT NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    is_grounded BOOLEAN NOT NULL DEFAULT TRUE,
    dense_candidates_count INTEGER NOT NULL DEFAULT 0,
    sparse_candidates_count INTEGER NOT NULL DEFAULT 0,
    reranked_chunks_count INTEGER NOT NULL DEFAULT 0,
    retrieval_latency_ms FLOAT NOT NULL DEFAULT 0.0,
    generation_latency_ms FLOAT NOT NULL DEFAULT 0.0,
    total_latency_ms FLOAT NOT NULL DEFAULT 0.0,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    citations_json JSONB DEFAULT '[]'::jsonb,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_queries_org_created ON rag_queries(organization_id, created_at DESC);
CREATE INDEX idx_rag_queries_user ON rag_queries(user_id, created_at DESC);
CREATE INDEX idx_rag_queries_session ON rag_queries(session_id);
```

#### 3.14.3 `rag_feedbacks` Table
Captures human user evaluation and satisfaction signals:
```sql
CREATE TABLE rag_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_id UUID NOT NULL REFERENCES rag_queries(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    is_helpful BOOLEAN NOT NULL DEFAULT TRUE,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_feedbacks_query ON rag_feedbacks(query_id);
CREATE INDEX idx_rag_feedbacks_org ON rag_feedbacks(organization_id, created_at DESC);
```


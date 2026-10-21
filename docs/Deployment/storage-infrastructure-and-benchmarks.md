# KEEP Enterprise Platform — Storage Infrastructure & Performance Benchmarks (Phase 1.8)

## 1. Architectural Overview & Tenant Isolation Model

The KEEP Document Management & Storage System (Phase 1.8) implements a high-throughput, multi-tenant digital asset repository architected for enterprise knowledge ingestion and RAG search pipelines.

```
+-----------------------------------------------------------------------------------------+
|                                    Client Request                                       |
|               (FastAPI /api/v1/documents/upload | download | preview)                   |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
                      +---------------------------------------------+
                      |       Authentication & Authorization        |
                      |   - JWT Token Subject Validation            |
                      |   - TenantContext (org_id resolution)       |
                      |   - Permission Checks (document.*)          |
                      +---------------------------------------------+
                                             |
                                             v
                      +---------------------------------------------+
                      |         DocumentValidator (Phase 1.8)       |
                      |   - NFKC Unicode Normalization              |
                      |   - Path Traversal Quarantine               |
                      |   - File Extension & Size Validation        |
                      |   - Magic Byte Sniffing (MIME Spoof Guard)  |
                      |   - SHA-256 Digest & Duplicate Check        |
                      +---------------------------------------------+
                                             |
                                             v
                      +---------------------------------------------+
                      |       LocalStorageService (Phase 1.8)       |
                      |   - Tenant-Isolated Filesystem Storage      |
                      |   - Strict Multi-Tenant Directory Hierarchy |
                      |   - Storage Quota Calculation & Enforcement |
                      |   - Preview Generation & Artifact Caching   |
                      +---------------------------------------------+
                                             |
                        +--------------------+--------------------+
                        |                                         |
                        v                                         v
         +-----------------------------+           +-----------------------------+
         |    PostgreSQL Persistence   |           |    Physical Storage Volume  |
         |  - documents (metadata)     |           |  storage_data:/app/storage  |
         |  - document_versions        |           |  - storage/{org_id}/docs/   |
         |  - activity_events (audit)  |           |  - storage/{org_id}/prevs/  |
         +-----------------------------+           +-----------------------------+
```

---

## 2. Docker Volume Mounting & Container Persistence

In containerized deployments, document binaries and cached preview artifacts reside on dedicated, Docker-managed named volumes to ensure zero data loss across container lifecycle events (restarts, image upgrades, and deployments).

### Docker Compose Volume Configuration (`docker-compose.yml`)

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    volumes:
      - ./backend:/app/backend
      - ./tests:/app/tests
      - ./uploads:/app/uploads
      - storage_data:/app/storage
    environment:
      STORAGE_ROOT: ${STORAGE_ROOT:-/app/storage}
      DEFAULT_STORAGE_QUOTA_BYTES: ${DEFAULT_STORAGE_QUOTA_BYTES:-10737418240}
      UPLOAD_STORAGE_PATH: /app/uploads

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  storage_data:
    driver: local
```

### Container Directory Permissions (`docker/Dockerfile.backend`)

```dockerfile
# Ensure uploads and storage directories exist and permissions are set for non-root appuser
RUN mkdir -p /app/uploads /app/storage && chown -R appuser:appgroup /app
USER appuser
```

---

## 3. Physical Storage Hierarchy & Path Sanitization

Documents and previews are stored in a partitioned filesystem hierarchy keyed strictly by `organization_id`:

```
/app/storage/
├── <organization_id_1>/
│   ├── documents/
│   │   └── <document_id_a>/
│   │       ├── v1/
│   │       │   └── quarterly_financials.pdf
│   │       └── v2/
│   │           └── quarterly_financials_revised.pdf
│   └── previews/
│       └── <document_id_a>/
│           ├── v1/
│           │   └── preview.pdf
│           └── v2/
│               └── preview.pdf
└── <organization_id_2>/
    └── documents/
        └── <document_id_b>/
            └── v1/
                └── employee_handbook.docx
```

### Path Traversal Defense Mechanisms (`DocumentValidator.sanitize_filename`)

- **NFKC Normalization**: Strips multi-byte bypass encodings.
- **Null-Byte Elimination**: Replaces `\0` to prevent filesystem truncation exploits.
- **Directory Stripping**: Uses `os.path.basename()` combined with regex replacement of `[\\/]+` and relative navigation sequences `\.\.+`.
- **Character Whitelist Sanitization**: Replaces POSIX and Windows forbidden characters `[:*?"<>|;&$]` with underscores.
- **Length Constraint**: Enforces a strict 255-character maximum length bound while preserving the valid file extension.

---

## 4. Security Boundaries & Threat Modeling

| Attack Vector | Defense Mechanism | Verified Status |
| :--- | :--- | :--- |
| **Cross-Tenant Data Leakage** | TenantContext multi-tenant row-level DB scoping (`get_by_id_and_org`) and isolated physical filesystem compartmentalization (`storage/{org_id}/`). Cross-tenant access returns 403 `AUTH_ORGANIZATION_MISMATCH` or 404 `DOCUMENT_NOT_FOUND`. | **Verified** (`test_01`) |
| **Directory Traversal (`../../`)** | `DocumentValidator.sanitize_filename()` strips all traversal tokens and resolves paths to enforce `Path.is_relative_to(tenant_root)`. | **Verified** (`test_02`) |
| **Storage Denial of Service (DoS)** | `LocalStorageService.check_quota()` verifies tenant byte usage against `DEFAULT_STORAGE_QUOTA_BYTES` before write; raises 400 `STORAGE_QUOTA_EXCEEDED`. | **Verified** (`test_03`) |
| **MIME Spoofing / Malicious Executables** | `DocumentValidator.sniff_magic_bytes()` checks ELF (`\x7fELF`), Windows PE (`MZ`), and shell headers against declared extensions; returns 422 `UNSUPPORTED_FILE_TYPE`. | **Verified** (`test_04`) |
| **Privilege Escalation / Unauthorized Deletion** | RBAC permission matrix checks `document.create`, `document.read`, `document.update`, `document.delete` and enforces ownership boundary (`uploader_id == caller.id` or OrgAdmin / Manager). | **Verified** (`test_05`) |
| **Duplicate Asset Injection** | SHA-256 cryptographic digest calculation per organization prevents duplicate file uploads, returning 409 `DUPLICATE_FILE_DETECTED`. Cross-org copies permitted. | **Verified** (`test_06`) |

---

## 5. Disaster Recovery & Backup/Restore Automation

### Storage Backup Procedure (`scripts/storage-backup.sh`)

Automates point-in-time snapshots of the document storage repository with cryptographic integrity verification:

```bash
# Execute local native backup
./scripts/storage-backup.sh --mode native

# Execute containerized backup
./scripts/storage-backup.sh --mode docker --output-dir /var/backups/keep --retention-days 14
```

Features:
- Compressed tar archive creation (`keep_storage_backup_YYYYMMDD_HHMMSS.tar.gz`).
- Automatic SHA-256 manifest generation (`keep_storage_manifest_YYYYMMDD_HHMMSS.sha256`).
- Automatic archive pruning adhering to retention policy (`--retention-days`).

### Storage Restoration Procedure (`scripts/storage-restore.sh`)

Restores an archived snapshot into the active storage root after integrity testing:

```bash
# Restore snapshot with integrity verification
./scripts/storage-restore.sh --file backups/storage/keep_storage_backup_20261021_191946.tar.gz --mode native --force
```

---

## 6. Performance SLAs & Benchmark Metrics

Target performance specifications defined in `devdocs/p1/p1.8.txt` Chapter 18:

| Operation | Target SLA | Benchmark Result (Measured) | Speedup Factor | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Upload Initiation** | `< 1000 ms` | **7.70 ms** (mean) / **24.11 ms** (peak) | **> 40x faster than SLA** | **PASS** |
| **Metadata Retrieval** | `< 500 ms` | **2.56 ms** (mean) / **5.65 ms** (peak) | **> 85x faster than SLA** | **PASS** |
| **Preview Streaming** | `< 5000 ms` | **2.67 ms** (mean) / **3.49 ms** (peak) | **> 1400x faster than SLA** | **PASS** |
| **Catalog List & Filter** | `< 500 ms` | **3.10 ms** (mean) / **3.88 ms** (peak) | **> 120x faster than SLA** | **PASS** |
| **Concurrent Uploads (8 threads)**| `100% Success` | **32.90 ms** / worker (100% 202 Accepted) | **Zero race conditions** | **PASS** |
| **Large Binary Throughput** | `> 50 MB/s` | **235.77 MB/s** (Upload) / **309.93 MB/s** (Download) | **Verified SHA-256 match** | **PASS** |

---

## 7. Operational Test Orchestration Script

Test execution is unified via `./scripts/test-document-management.sh`:

```bash
# Run complete test suite (security, performance, backend API, frontend)
./scripts/test-document-management.sh all

# Target specific test suites
./scripts/test-document-management.sh security
./scripts/test-document-management.sh perf
./scripts/test-document-management.sh backend
./scripts/test-document-management.sh frontend
./scripts/test-document-management.sh e2e
```

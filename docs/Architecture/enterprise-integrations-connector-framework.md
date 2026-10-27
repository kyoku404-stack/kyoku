# KEEP — Enterprise Integrations & Connector Framework Architecture Specification (Phase 3.1)

## 1. Executive Summary & Objective
Modern enterprises store mission-critical organizational knowledge across disparate, siloed SaaS platforms—cloud storage systems (Google Drive, Microsoft OneDrive, SharePoint), communication suites (Slack, Microsoft Teams), source code repositories (GitHub, GitLab), project management tools (Jira, Confluence, Notion), and CRM platforms (Salesforce, HubSpot). This fragmentation causes employee productivity loss and blind spots in AI decision support.

**Phase 3.1** establishes the **Enterprise Integration & Connector Framework** for KEEP. By introducing an extensible, secure, multi-tenant Integration Gateway, KEEP continuously harmonizes external documents, chats, tickets, and code into its internal RAG, Vector Search, and Knowledge Graph pipelines while preserving document provenance, external metadata, and source platform permissions.

---

## 2. High-Level Architecture Diagram

```
                 External Enterprise Platforms
   ┌───────────────┬─────────────────┬──────────────┬──────────────┐
   │ Google Drive  │ SharePoint/M365 │ GitHub / Git │ Slack/Teams  │
   └───────┬───────┴────────┬────────┴──────┬───────┴──────┬───────┘
           │                │               │              │
           └────────────────┼───────────────┼──────────────┘
                            ▼
              ┌───────────────────────────┐
              │    Integration Gateway    │
              └─────────────┬─────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │   Connector Management Layer    │
           │  (Registration, Status, Quota)  │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │     Authentication Manager      │
           │ (OAuth2, Tokens, Fernet Crypto) │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │     Synchronization Engine      │
           │ (Full, Incremental, Change Det) │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │    Data Transformation Layer    │
           │ (Normalizer, Metadata, RBAC Map)│
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │   KEEP AI Knowledge Pipeline    │
           │ (Ingestion, Chunking, Embeddings│
           │  Vector DB & Knowledge Graph)   │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │      Unified Enterprise AI      │
           │   RAG Search & Assistant Hub    │
           └─────────────────────────────────┘
```

---

## 3. Supported Platforms & Categorization Matrix

| Category | Platform ID | Primary Auth Methods | Typical Resources Ingested |
| :--- | :--- | :--- | :--- |
| **Cloud Storage** | `google_drive` | OAuth 2.0, Service Account | Docs, Sheets, Slides, PDFs, Text files |
| **Cloud Storage** | `onedrive` | OAuth 2.0 (Azure AD) | Word, Excel, PowerPoint, PDFs, Files |
| **Cloud Storage** | `sharepoint` | OAuth 2.0, App Principal | Document Libraries, Site Pages, Lists |
| **Cloud Storage** | `dropbox` | OAuth 2.0 | Team folders, shared files |
| **Cloud Storage** | `s3` | API Keys (Access/Secret Key) | Object storage buckets, unstructured data |
| **Documentation** | `confluence` | OAuth 2.0, Personal Access Token | Spaces, Pages, Blog posts, Attachments |
| **Documentation** | `notion` | OAuth 2.0, Internal Integration Token | Workspaces, Databases, Pages, Blocks |
| **Communication** | `slack` | OAuth 2.0 (Bot/User Token) | Public/Private Channels, Canvas, Threads |
| **Communication** | `teams` | OAuth 2.0 (Graph API) | Team channels, Chat history, Shared docs |
| **Development** | `github` | OAuth 2.0, Personal Access Token | Repositories, READMEs, PR discussions, Issues |
| **Development** | `gitlab` | Personal Access Token, OAuth 2.0 | Project docs, Repositories, Issue boards |
| **Project Mgmt** | `jira` | OAuth 2.0, API Token | Projects, Epics, Issues, Sprint retro boards |
| **CRM** | `salesforce` | OAuth 2.0 | Knowledge articles, Account briefs, Notes |
| **CRM** | `hubspot` | OAuth 2.0, Private App Token | Knowledge Base, Company notes, Tickets |

---

## 4. Connector Lifecycle State Machine

Each integrated connector transitions through a deterministic lifecycle:
```
           ┌──────────────┐
           │  REGISTERED  │ (Metadata and config stored)
           └──────┬───────┘
                  │
                  ▼
         ┌──────────────────┐
         │  AUTHENTICATING  │ (OAuth handshake or token validation)
         └────────┬─────────┘
                  ├────────────────────────────┐
                  │ (Success)                  │ (Failure)
                  ▼                            ▼
           ┌──────────────┐             ┌──────────────┐
           │  CONNECTED   │             │    ERROR     │
           └──────┬───────┘             └──────────────┘
                  │
                  ▼
           ┌──────────────┐
           │   SYNCING    │ (Background job executing: Full or Incremental)
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │   HEALTHY    │ (Sync finished successfully, last_sync_at updated)
           └──────────────┘
```

---

## 5. Authentication & Secret Protection Architecture

All connector credentials (OAuth Refresh Tokens, Access Tokens, API Keys, Webhook Secrets) must NEVER be stored in plain text.
1. **Encryption Standard**: Credentials are encrypted at rest using Fernet symmetric encryption (AES-128 in CBC mode with HMAC-SHA256 authenticated encryption) derived from the application secret `SECRET_KEY`.
2. **Tenant Isolation**: Encryption keys and credential envelopes are scoped strictly per `organization_id`.
3. **Token Refresh Workflow**: When token expiration is detected ($t \le 300\text{s}$ to expiry), the Authentication Manager automatically exchanges the refresh token with the upstream identity provider before initiating sync operations.

---

## 6. Incremental Change Detection & Checksum Engine

To maintain sync speed ($< 2$ minutes for incremental syncs) and avoid redundant processing of gigabytes of unmodified data:
1. **Delta Fingerprinting**:
   Each ingested resource calculates a content checksum:
   $$\text{Checksum} = \text{SHA-256}(\text{Raw Content Body} + \text{MIME Type})$$
2. **Comparison Logic**:
   - **NEW**: Resource ID not found in connector's sync index.
   - **UPDATED**: Resource ID exists, but external `modified_at` is newer OR `Checksum` $\ne$ stored checksum.
   - **DELETED**: Resource ID was previously synchronized but is omitted from external listing / returns 404.
   - **UNCHANGED**: Identical Checksum and unmodified timestamp; skipped without re-indexing.
3. **Permission Delta**:
   If external ACLs change (e.g. file unshared from public to team-only), the permission mapping is immediately updated without requiring full chunk re-embedding.

---

## 7. Data Normalization & Metadata Preservation

External resources are normalized into the standard KEEP ingestion envelope:
```json
{
  "external_id": "gdrive-doc-98124",
  "source_platform": "GOOGLE_DRIVE",
  "source_url": "https://docs.google.com/document/d/98124/edit",
  "title": "Q3 Engineering Roadmap",
  "raw_content": "# Q3 Engineering Roadmap\n\n...",
  "mime_type": "text/markdown",
  "author": "sarah.chen@enterprise.com",
  "department": "Engineering",
  "tags": ["roadmap", "q3", "planning"],
  "external_created_at": "2026-06-15T09:00:00Z",
  "external_modified_at": "2026-07-20T14:30:00Z",
  "permission_level": "READ",
  "allowed_roles": ["OrgAdmin", "Manager", "Member"],
  "checksum": "a8f3b2...",
  "version": "4"
}
```

---

## 8. Cross-Platform Permission Mapping

External access levels are mapped into KEEP RBAC primitives:

| External Platform Role | Normalized Level | KEEP RBAC Roles Allowed |
| :--- | :--- | :--- |
| Owner / Admin / Workspace Admin | `OWNER` / `ADMIN` | `SuperAdmin`, `OrgAdmin` |
| Editor / Contributor / Writer | `WRITE` / `EDITOR` | `OrgAdmin`, `Manager` |
| Viewer / Reader / Channel Member | `READ` / `VIEWER` | `OrgAdmin`, `Manager`, `Member` |
| Public / Domain-Wide Shared | `PUBLIC` | `SuperAdmin`, `OrgAdmin`, `Manager`, `Member`, `Guest` |

---

## 9. Integration Dashboard & Monitoring Metrics

The Integration Dashboard surfaces key telemetry for administrative governance:
- **Total Registered Connectors**: Count by platform type and health state.
- **Sync Success Rate**: Ratio of completed sync jobs over total runs.
- **Documents Synchronized**: Cumulative ingested resources per platform.
- **API Latency & Health**: Response times ($< 5000\text{ms}$ SLA target).
- **Error Log Feed**: Chronological failure diagnostics with actionable retry actions.

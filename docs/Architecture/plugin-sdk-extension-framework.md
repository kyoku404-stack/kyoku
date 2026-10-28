# Architecture Specification: Plugin SDK, Extension Framework & Developer Ecosystem

> **Phase**: 3.5  
> **Author**: Member 1 (Project Lead & AI Architect)  
> **Status**: DRAFT / APPROVED FOR IMPLEMENTATION  
> **Domain**: `/docs/Architecture/plugin-sdk-extension-framework.md`  
> **Specification Reference**: `devdocs/p3/p3.5.txt` (Chapters 1–20)

---

## 1. Executive Summary & Architectural Goals

The KEEP Plugin SDK and Extension Framework establishes an enterprise-grade extension layer enabling organizations, external developers, and system integrators to extend KEEP capabilities without modifying core system source code.

### Core Architectural Goals
1. **Modular Extensibility**: Support independent plugins across five distinct categories: AI Plugins, Integration Plugins, Workflow Plugins, UI Plugins, and Analytics Plugins.
2. **Process & Resource Sandboxing**: Isolate plugin execution from core database transactions and critical OS processes with strict capability-based permissions and CPU/memory/network quotas.
3. **Event-Driven Extension Hooks**: Enable reactive plugins to listen and hook into core system events (`document.uploaded`, `ai.query.generated`, `workflow.step.completed`, `user.login`) via an asynchronous hook broker.
4. **Manifest-Driven Semantic Compatibility**: Validate plugin metadata, required permissions, runtime dependencies, and API version compatibility using strict SemVer specifications.
5. **Decentralized & Managed Marketplace**: Provide a centralized catalog interface supporting discovery, verification badges, version rollbacks, and enterprise-internal publishing.
6. **Developer Ergonomics**: Provide a typed Python SDK, manifest schema validation, CLI development tools, and mock extension test harnesses.

---

## 2. High-Level System Architecture

```
                    ┌────────────────────────────────────────────────┐
                    │               KEEP Core Platform               │
                    │  (FastAPI, Auth, PostgreSQL, Vector, Workflows)│
                    └───────────────────────┬────────────────────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │            Plugin Management Layer             │
                    │   - Manifest Validator   - Sandbox Manager     │
                    │   - Permission Broker    - Hook Dispatcher     │
                    └───────┬───────────────┬────────────────┬───────┘
                            │               │                │
            ┌───────────────▼┐      ┌───────▼────────┐      ┌▼───────────────┐
            │   AI Plugins   │      │  Integrations  │      │   UI Plugins   │
            │ - Custom LLMs  │      │ - CRM/ERP SaaS │      │ - Custom Cards │
            │ - Embeddings   │      │ - Cloud Storage│      │ - Dashboards   │
            │ - Custom Rerank│      │ - Ticketing    │      │ - Brand Themes │
            └───────┬────────┘      └───────┬────────┘      └┬───────────────┘
                    │                       │                │
                    └───────────────┬───────┴────────────────┘
                                    ▼
                    ┌────────────────────────────────────────────────┐
                    │           Event & Hook Orchestrator            │
                    │   - document.uploaded    - user.authenticated  │
                    │   - workflow.completed   - ai.response.ready   │
                    └───────────────────────┬────────────────────────┘
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │          Sandboxed Execution Engine            │
                    │   - Isolated Subprocess / In-Process Worker    │
                    │   - Timeout Enforcement & Memory Guardrails    │
                    │   - Audit & Telemetry Logging                  │
                    └────────────────────────────────────────────────┘
```

---

## 3. Plugin Categories & Extension Surface

| Category | Typical Use Cases | Extension Surface | Key Interfaces |
| :--- | :--- | :--- | :--- |
| **AI Plugins** | Custom local LLMs, proprietary embedding models, domain OCR, translation | `backend/app/services/plugins/ai` | `BaseLLMPluginAdapter`, `BaseEmbeddingPluginAdapter` |
| **Integration Plugins** | Enterprise ERPs, proprietary databases, bespoke storage APIs | `backend/app/services/plugins/integrations` | `BaseIntegrationPluginAdapter`, `BaseSyncAdapter` |
| **Workflow Plugins** | Custom workflow action nodes, specialized approvals, compliance checkers | `backend/app/services/plugins/workflows` | `BaseWorkflowActionPlugin`, `BaseRuleEvaluator` |
| **UI Plugins** | Dashboard metric widgets, specialized graph renderers, custom themes | `frontend/src/features/plugins` | `UIWidgetDescriptor`, `ThemeConfig` |
| **Analytics Plugins** | Domain KPI estimators, forecasting models, predictive reporting | `backend/app/services/plugins/analytics` | `BaseAnalyticsCalculator`, `MetricReportEngine` |

---

## 4. Plugin Lifecycle State Machine

Plugins progress through deterministic lifecycle stages. Every transition generates immutable audit telemetry.

```
       [INSTALL] ──► [VALIDATE] ──► [INITIALIZE]
                           │
                           ▼ (Invalid Manifest / Missing Permission)
                        [ERROR]
                           ▲
                           │
  ┌────────────────────────┴───────────────────────────┐
  │                                                    │
  ▼                                                    │
[INACTIVE] ───(Enable)───► [ACTIVE] ───(Execute)───► [RUNNING]
  ▲                           │                         │
  │                           │                         │
  │                           ▼                         ▼
  └───────(Disable)─────── [PAUSED] ◄────(Timeout/Err)──┘
                              │
                              ▼
                         [UNINSTALLED]
```

1. **Install**: Plugin package/tarball is received, unpacked into tenant storage, and registered in `plugins`.
2. **Validate**: Manifest schema, semantic version compatibility, checksums, and dependencies are verified.
3. **Initialize**: Configuration defaults are seeded, permissions are recorded, and event hook bindings are registered.
4. **Active / Enabled**: Sandboxed workers are instantiated or registered in the in-memory hook router.
5. **Execute / Running**: Plugin runs actions in response to direct API invocation or dispatched platform events.
6. **Disable / Paused**: Event subscriptions are detached; execution requests are rejected with 403.
7. **Uninstall**: All hooks, configuration, and tenant installations are removed; audit log retained.

---

## 5. Security Sandboxing & Capability-Based Permissions

### 5.1 Sandboxing Guarantees
- **No Direct Database Access**: Plugins communicate strictly through authenticated platform API tokens or mediator interfaces. Direct SQL injection or raw DB sessions are architecturally forbidden.
- **Resource Constraints**:
  - Maximum execution timeout: 30 seconds default (configurable up to 300s).
  - CPU usage cap and memory limit (configurable max 512MB per plugin worker).
  - Output payload size cap (max 10MB per step).
- **Network Boundaries**: Outbound network requests require explicit `Network.Outbound` capability declarations in the manifest.

### 5.2 Granular Capability Permissions
```json
{
  "permissions": [
    "Documents.Read",
    "Documents.Write",
    "AI.Query",
    "Analytics.Read",
    "Notifications.Send",
    "Workflow.Execute",
    "Graph.Read",
    "Network.Outbound"
  ]
}
```

---

## 6. Manifest Specification Schema

Each plugin must bundle a valid `plugin.json` manifest conforming to JSON Schema Draft 7:

```json
{
  "id": "enterprise-sap-connector",
  "name": "SAP S/4HANA Enterprise Connector",
  "version": "1.2.0",
  "developer": "Acme Integrations Inc.",
  "description": "Bi-directional document synchronization and invoice indexing for SAP S/4HANA.",
  "category": "INTEGRATION",
  "api_version": "v1",
  "min_keep_version": "3.0.0",
  "max_keep_version": "3.9.9",
  "entry_point": "sap_connector.plugin:SAPPlugin",
  "permissions": [
    "Documents.Read",
    "Documents.Write",
    "Notifications.Send",
    "Network.Outbound"
  ],
  "event_hooks": [
    "document.uploaded",
    "workflow.step.completed"
  ],
  "configuration_schema": {
    "type": "object",
    "properties": {
      "endpoint_url": { "type": "string", "format": "uri" },
      "client_id": { "type": "string" },
      "sync_interval_minutes": { "type": "integer", "default": 60 }
    },
    "required": ["endpoint_url", "client_id"]
  }
}
```

---

## 7. Event Hook Subscription Model

The `PluginHookDispatcher` operates on an asynchronous event broker:
1. When a core platform event triggers (`document.uploaded`), the dispatcher queries all active plugins registered for that event topic.
2. For each subscribed plugin:
   - Evaluates whether the tenant has enabled the plugin.
   - Verifies plugin permissions include the event scope.
   - Executes the hook within a sandboxed timeout boundary (`asyncio.wait_for`).
   - Collects response or catches errors without blocking other subscribers or core workflows.
3. Detailed execution latency and error codes are persisted to `plugin_execution_logs`.

---

## 8. Marketplace Architecture & Verification Tiers

The Marketplace serves as the discovery engine for internal and public plugins:
- **Verification Tiers**:
  - `VERIFIED`: Formally reviewed and signed by KEEP security team.
  - `COMMUNITY`: Open-source or third-party verified plugin.
  - `INTERNAL`: Custom organization-authored proprietary plugin.
- **Metrics Tracked**:
  - Download count, average rating (1–5 stars), active installs, error rate, and vulnerability scan status.
- **Version Compatibility Matrix**:
  - Prevents installation if current KEEP platform version does not satisfy `min_keep_version` <= `CURRENT_VERSION` <= `max_keep_version`.

---

## 9. Performance & SLA Benchmarks

- **Plugin Initialization**: < 2.0s p95
- **Plugin Installation & Validation**: < 5.0s p95
- **Event Hook Execution Overhead**: < 100ms p95
- **Plugin Update / Rollback**: < 10.0s p95
- **Concurrent Active Plugins per Tenant**: Up to 50 active plugins with isolated resource budgets

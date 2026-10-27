# KEEP — Enterprise Intelligence, Predictive Analytics & Knowledge Health Architecture Specification (Phase 2.5)

## 1. Executive Summary & Objective
Phase 2.5 establishes the **Enterprise Intelligence & Predictive Analytics** module within the KEEP platform. While earlier phases focused on ingestion, search, agentic workflows, and knowledge graph construction, Phase 2.5 aggregates this operational footprint into continuous decision support. It continuously computes:
1. **Multi-Dimensional Knowledge Health Score (KHS)**: Real-time quantification (0–100) of organizational knowledge coverage, freshness, document quality, duplicate redundancy, and retrieval efficacy.
2. **Predictive Analytics & Forecasting Engine**: Statistical time-series regression models with confidence intervals estimating expected document volume, storage runway, AI query demand, and project completion milestones.
3. **Automated Anomaly Detection**: Statistical Z-score and IQR-based monitoring discovering unusual operational swings (e.g. abrupt drops in cross-department collaboration, abnormal document deletions, spike in retrieval failures).
4. **Contextual Strategic Recommendation Engine**: Heuristic and AI-driven recommendations prioritized by business impact vs effort (e.g., archiving stale docs, deduplicating parallel knowledge, assigning orphan topic owners).
5. **Executive Intelligence Dashboard**: Real-time KPI summaries, trend graphs, and natural-language executive briefings.

---

## 2. High-Level Architecture Diagram

```
                 Multi-Tenant Enterprise Operational Data
 (Documents, Projects, Meetings, Knowledge Graph, Activity Logs, RAG Queries)
                                   │
                                   ▼
                   Data Aggregation & Snapshot Layer
               (Tenant Context Isolation, Redis Cache 300s)
                                   │
                                   ▼
        ┌────────────────────────────────────────────────────────┐
        │       Enterprise Intelligence Processing Engine        │
        └──────────────────────────┬─────────────────────────────┘
                                   │
     ┌───────────────┬─────────────┴───────────────┬────────────────┐
     ▼               ▼                             ▼                ▼
Knowledge Health   Predictive Forecasting   Anomaly Detector   Strategic Recs
 Score (KHS)       (Linear Regression/SE)   (Z-Score / IQR)    (Impact/Effort)
     │               │                             │                │
     └───────────────┼─────────────────────────────┴────────────────┘
                     ▼
       Executive Intelligence Dashboard APIs & Visualizations
      (/api/v1/analytics/dashboard, /kpis, /trends, /predictions)
```

---

## 3. Mathematical Formulations & Algorithms

### 3.1 Multi-Dimensional Knowledge Health Score (KHS)
The Knowledge Health Score $KHS \in [0, 100]$ evaluates institutional knowledge fitness:

$$KHS = \min(100, \max(0, w_{cov} C_{cov} + w_{fresh} C_{fresh} + w_{qual} C_{qual} + w_{ret} C_{ret} - P_{dup} C_{dup}))$$

Where standard weights sum to 100:
- $w_{cov} = 30$: Knowledge Coverage across registered departments and projects.
  $$C_{cov} = \frac{|\text{Departments with Active Docs}|}{|\text{Total Departments}|} \times 100$$
- $w_{fresh} = 25$: Knowledge Freshness based on last updated timestamp:
  $$C_{fresh} = \frac{|\text{Docs updated in last 90 days}|}{|\text{Total Documents}|} \times 100$$
- $w_{qual} = 25$: Documentation Quality (content completeness, chunk density, metadata tags).
- $w_{ret} = 20$: Retrieval Effectiveness (mean RAG confidence score and user satisfaction rate).
- $P_{dup} = 15$: Duplicate/Stale Penalty based on high vector cosine similarity (> 0.95) among chunks.

#### Health Score Tiers:
- **Excellent**: $KHS \ge 85$ (Green)
- **Good**: $70 \le KHS < 85$ (Emerald/Blue)
- **Fair**: $50 \le KHS < 70$ (Amber)
- **At Risk**: $KHS < 50$ (Rose/Red)

---

### 3.2 Predictive Analytics & Forecasting
Given historical observations $(t_i, y_i)$ over $N$ days/weeks, the system computes the slope $\beta$ and intercept $\alpha$ via ordinary least squares (OLS):

$$\beta = \frac{\sum (t_i - \bar{t})(y_i - \bar{y})}{\sum (t_i - \bar{t})^2}, \quad \alpha = \bar{y} - \beta \bar{t}$$

For horizon $h$ steps ahead, projected value:
$$\hat{y}(t + h) = \alpha + \beta (t + h)$$

Confidence interval bounds ($\pm 1.96 \cdot \text{SE}$ for 95% confidence):
$$\text{SE} = \sqrt{\frac{1}{N-2} \sum (y_i - \hat{y}_i)^2}$$

Forecast Targets:
1. **Document Ingestion Growth**: Expected document counts across 30, 60, 90 days.
2. **Storage Capacity Depletion**: Projected date when storage reaches 85% and 95% capacity limits.
3. **AI Query Volume**: Expected RAG query consumption for token budget planning.

---

### 3.3 Anomaly Detection Pipeline
For key operational time series $x_t$ (e.g. daily logins, documents uploaded, RAG queries, cross-team citations), the system computes:
$$\mu = \frac{1}{W} \sum_{i=1}^W x_{t-i}, \quad \sigma = \sqrt{\frac{1}{W} \sum_{i=1}^W (x_{t-i} - \mu)^2}$$
$$Z_t = \frac{|x_t - \mu|}{\sigma}$$

- **LOW**: $1.5 \le Z_t < 2.0$
- **MEDIUM**: $2.0 \le Z_t < 2.5$
- **HIGH**: $2.5 \le Z_t < 3.0$
- **CRITICAL**: $Z_t \ge 3.0$ (or > 50% single-day drop in active collaboration).

---

### 3.4 Strategic Recommendation Scoring
Recommendations are scored via Priority Index ($PI$):
$$PI = \frac{\text{Impact Score} (1-10) \times 1.5}{\text{Effort Score} (1-5)}$$

Categories:
- `ARCHIVE`: Inactive or obsolete documents with 0 views or queries over 180 days.
- `DEDUPLICATE`: Documents with semantic similarity > 0.92 requiring consolidation.
- `COVERAGE`: Departments or initiatives with 0 indexed documentation.
- `OWNERSHIP`: Orphan knowledge graph nodes lacking an assigned employee or team lead.
- `COLLABORATION`: Teams with high operational overlap but 0 shared projects.

---

## 4. Multi-Tenant Security & RBAC Isolation
1. **Tenant Quarantining**: All aggregations are strictly filtered by `organization_id`. Cross-tenant metrics never leak into trend lines or prediction models.
2. **Role Boundaries**:
   - `Viewer`, `Member`: Access to general trends and their own department KPIs.
   - `Manager`: Access to team health scores, anomalies, and departmental forecasts.
   - `OrgAdmin`, `SuperAdmin`: Full executive dashboard, organization-wide KHS, risk indicators, and recommendation triage.

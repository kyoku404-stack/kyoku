# KEEP — Retrieval-Augmented Generation (RAG) Engine & Semantic Search Architecture

> **Master Architecture Specification — Phase 2.2**  
> *Author: Member 1 (Project Lead & AI Architect)*  
> *Reference: `devdocs/p2/p2.2.txt`, `AGENT_RULES.md`, `ARCHITECTURE.md`*

---

## 1. Executive Summary & Objective

Phase 2.2 transforms KEEP from an AI-ready document repository into an enterprise-grade, explainable question-answering intelligence platform. The system implements a resilient, multi-stage Retrieval-Augmented Generation (RAG) pipeline that guarantees **multi-tenant security**, **zero-hallucination guardrails**, and **verifiable citation provenance**.

Every generated answer is strictly grounded in organizational knowledge retrieved via hybrid semantic-keyword search, neural reranking, token-budgeted context assembly, and LLM synthesis.

```
                           +─────────────────────────────────────────+
                           |           User Natural Query            |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |          Query Understanding            |
                           |  - Intent classification                |
                           |  - Acronym & entity expansion           |
                           |  - Organization security scoping        |
                           +─────────────────────────────────────────+
                                                │
                                ┌───────────────┴───────────────┐
                                ▼                               ▼
                  +───────────────────────────+   +───────────────────────────+
                  |    Dense Vector Search    |   |   Sparse Full-Text Search |
                  |  - pgvector HNSW cosine   |   |  - PostgreSQL tsvector    |
                  |  - text-embedding-3-small |   |  - websearch_to_tsquery   |
                  |  - L2-normalized 1536-dim |   |  - Exact phrase & keyword |
                  +───────────────────────────+   +───────────────────────────+
                                │                               │
                                └───────────────┬───────────────┘
                                                ▼
                           +─────────────────────────────────────────+
                           |     Reciprocal Rank Fusion (RRF)        |
                           |  Combines & normalizes candidate ranks  |
                           |  RRF_Score(d) = sum(1 / (k + rank_i))   |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |       Neural & Heuristic Reranker       |
                           |  - Cross-Encoder relevance score        |
                           |  - Freshness & department priority      |
                           |  - Top K=5 selected high-signal chunks  |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |             Context Builder             |
                           |  - Token budgeting (max 3,000 tokens)   |
                           |  - Deduplication & structural assembly  |
                           |  - Multi-turn conversation history      |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |   LLM Generation & Grounding Engine     |
                           |  - Strict system prompt guardrails      |
                           |  - Grounded answer synthesis            |
                           |  - Inline citation tags [Doc X, Page Y] |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |         Citation Verification           |
                           |  - Verifies cited chunk IDs vs context  |
                           |  - Confidence score calculation         |
                           |  - Fallback refusal if confidence < 0.6 |
                           +─────────────────────────────────────────+
                                                │
                                                ▼
                           +─────────────────────────────────────────+
                           |   Grounded Response with Citations      |
                           +─────────────────────────────────────────+
```

---

## 2. Mathematical Formulations & Core Algorithms

### 2.1 Hybrid Retrieval Fusion: Reciprocal Rank Fusion (RRF)
To fuse heterogeneous rank lists from dense vector search ($R_{\text{dense}}$) and sparse full-text search ($R_{\text{sparse}}$) without score scale distortion, the pipeline computes:

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{w_m}{k + r_m(d)}$$

Where:
- $w_{\text{dense}} = 0.65$ and $w_{\text{sparse}} = 0.35$ (default hybrid weights, configurable per query).
- $r_m(d)$ is the 1-based rank index of chunk $d$ in result set $m$. If chunk $d$ does not appear in set $m$, its penalty rank is $r_m(d) = \infty$, yielding $0$ contribution.
- $k$ is the smoothing constant, set to $60$ (standard TREC / IR evaluation benchmark).

### 2.2 Result Reranking Formula
Given the top $N = 25$ candidate chunks from RRF, the reranker calculates a composite relevance score:

$$\text{FinalScore}(d, q) = \alpha \cdot S_{\text{cross}}(q, d) + \beta \cdot S_{\text{freshness}}(d) + \gamma \cdot S_{\text{scope}}(d, u)$$

Where:
- $S_{\text{cross}}(q, d) \in [0, 1]$ is the neural cross-encoder semantic score (or normalized bi-encoder dot-product).
- $S_{\text{freshness}}(d) = \exp\left(-\frac{\Delta t}{\tau}\right)$ where $\Delta t$ is days since document version creation and half-life $\tau = 180$ days.
- $S_{\text{scope}}(d, u) \in \{0.0, 0.5, 1.0\}$ gives a relevance boost if the document matches the querying user's department or project.
- Weights: $\alpha = 0.70$, $\beta = 0.15$, $\gamma = 0.15$.

### 2.3 Hallucination Prevention & Confidence Scoring
To prevent hallucinations, the engine computes a composite **Context Confidence Score**:

$$\text{Confidence}(Q, C) = \frac{1}{|C_K|} \sum_{c \in C_K} \text{FinalScore}(c, Q)$$

- If $\text{Confidence} < 0.35$, the system triggers the **Zero-Hallucination Circuit Breaker**:
  *"I could not find sufficient authoritative information in your organization's documents to answer this question accurately. Please verify your query or upload the relevant document."*
- If $\text{Confidence} \ge 0.35$, the LLM is instructed to generate the response strictly using the provided context chunks.

---

## 3. Query Understanding & Normalization
Before dispatching queries to the retrieval engine:
1. **Acronym Expansion**: Replaces enterprise abbreviations based on organization taxonomy (e.g., `WFH` $\rightarrow$ `Work From Home`, `PTO` $\rightarrow$ `Paid Time Off`, `NDA` $\rightarrow$ `Non-Disclosure Agreement`).
2. **Intent Classification**:
   - `FACTUAL_LOOKUP`: Direct policy, specification, or numeric query $\rightarrow$ hybrid search with high sparse weight.
   - `SUMMARY_SYNTHESIS`: "Summarize", "Overview", "Explain" $\rightarrow$ semantic search prioritized, larger chunk retrieval.
   - `COMPARISON`: "Compare X and Y" $\rightarrow$ multi-entity multi-vector retrieval.
   - `CONVERSATIONAL_FOLLOWUP`: Pronoun resolution using conversation memory.
3. **Coreference Resolution**: If the query contains anaphora ("Who approves it?"), the context builder injects the last user question and assistant answer to formulate an expanded standalone query.

---

## 4. Multi-Tenant Security & Access Control
- All queries **strictly inject** the authenticated user's `organization_id` into vector queries and full-text searches.
- Role-based document access checks (`can_access_document`) ensure that confidential/restricted documents are filtered out before reaching context assembly.
- Cross-tenant data leakage is structurally impossible at the SQL / vector store query layer.

---

## 5. Context Builder & Token Budget Architecture
- **Max Context Budget**: 3,000 tokens reserved for retrieved chunks (leaving 1,000 tokens for system instructions, conversation history, and generation buffer within 4,096/8,192 token windows).
- **Chunk Deduplication**: If multiple overlapping chunks originate from the same document section, redundant spans are pruned.
- **Ordering**: Highest-scoring chunks are placed at the beginning and end of the context block to exploit LLM attention primacy and recency biases ("Lost in the Middle" mitigation).
- **Metadata Injection**: Each chunk is prefixed with an XML or markdown header:
  ```markdown
  [Document 1: Employee Handbook.pdf (v1.0) | Page 18 | Section 4.2 | ID: chunk_123]
  All full-time employees are eligible for 20 days of paid annual leave...
  ```

---

## 6. Citation Generation & Provenance Protocol
- Every statement containing factual assertions cites its source chunk using bracketed markers `[1]`, `[2]` or `[Doc 1, Page 18]`.
- Post-generation, the Citation Engine maps every marker back to the specific `DocumentChunk` and constructs structured citation objects:
  ```json
  {
    "citation_id": "cit_abc123",
    "document_id": "d3b07384-d113-46fb-a0b4-eb40a3f7ff95",
    "document_title": "Employee Handbook.pdf",
    "document_version_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "page_number": 18,
    "section": "Section 4.2: Paid Annual Leave",
    "chunk_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "similarity_score": 0.892,
    "excerpt": "All full-time employees are eligible for 20 days of paid annual leave..."
  }
  ```

---

## 7. Conversational Memory Specification
- **Session Model**: `ChatSession` tracks multi-turn dialogues identified by `session_id`.
- **History Window**: Sliding window of the last 10 messages (5 turns) maintained to preserve conversational coherence without exhausting the context budget.
- **Persistence**: Stored in PostgreSQL with full relational integrity to `users` and `organizations`.

---

## 8. Performance SLA Matrix
| Metric | Target SLA | Strategy |
| :--- | :--- | :--- |
| Semantic Vector Search | $< 150\text{ ms}$ | HNSW index on pgvector with `m=16, ef_search=40` |
| Sparse Full-Text Search | $< 50\text{ ms}$ | GIN index on `tsvector` |
| RRF Fusion & Reranking | $< 100\text{ ms}$ | In-memory vectorized ranking |
| Context Assembly | $< 20\text{ ms}$ | Lightweight string builder with token counter |
| LLM Time-to-First-Token | $< 1,200\text{ ms}$ | Streaming SSE response |
| Overall End-to-End Latency | $< 3,500\text{ ms}$ | Parallel retrieval + streaming generation |

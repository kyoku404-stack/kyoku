"""KEEP Phase 4.3 — Deterministic Specialist Agents for Multi-Agent Orchestration.

Provides four registered KEEP agents conforming strictly to Phase 4.1's `BaseAgent`
Protocol (`knowledge_retrieval`, `knowledge_analysis`, `decision_extractor`,
`risk_analyzer`) so Phase 4.3 sequential, conditional, and parallel workflows execute
deterministically through Phase 4.2 `AgentRuntime` without requiring live LLM keys.

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Sections 6, 7, 15)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import (
    AgentContext,
    AgentRequest,
    AgentResult,
    EvidenceReference,
)
from backend.app.agents.errors import AgentErrorCode
from backend.app.agents.metadata import AgentCapability, AgentMetadata


class KnowledgeRetrievalAgent:
    """Retrieves tenant-authorized organizational documents relevant to a workflow goal."""

    def __init__(self) -> None:
        self._metadata = AgentMetadata(
            agent_id="knowledge_retrieval",
            name="KEEP Knowledge Retrieval Agent",
            version="1.0.0",
            description="Retrieves tenant-authorized documents and grounded excerpts for downstream analysis.",
            capabilities=[
                AgentCapability(
                    name="knowledge.search",
                    description="Search tenant-authorized enterprise documents.",
                    access="read",
                )
            ],
            tags=["phase-4.3", "retrieval", "orchestration"],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        project_id = str(request.input.get("project_id") or request.input.get("topic") or "enterprise-core")

        # Deterministic no-evidence path for testing conditional routing
        if request.input.get("force_no_evidence") is True or project_id.lower() in (
            "empty",
            "no-evidence",
            "unknown-project",
        ):
            return AgentResult(
                status="succeeded",
                output={
                    "query": request.goal,
                    "topic": project_id,
                    "document_count": 0,
                    "summary": f"No authorized documents matched topic '{project_id}'.",
                },
                evidence=[],
                warnings=["No matching authorized evidence found for this request."],
            )

        evidence = [
            EvidenceReference(
                source_id=f"doc_{project_id}_decisions",
                source_type="document",
                title=f"{project_id} — Architecture & Decision Log",
                excerpt=(
                    f"Approved decision: adopt zero-trust multi-agent orchestration for {project_id} "
                    f"(owner: Platform Lead, tenant={context.tenant_id})."
                ),
                score=0.95,
                tenant_id=context.tenant_id,
            ),
            EvidenceReference(
                source_id=f"doc_{project_id}_risks",
                source_type="document",
                title=f"{project_id} — Operational Risk Register",
                excerpt=(
                    f"Identified risk: downstream provider timeout and stale checkpoint recovery "
                    f"mitigated via bounded retries (tenant={context.tenant_id})."
                ),
                score=0.91,
                tenant_id=context.tenant_id,
            ),
        ]

        return AgentResult(
            status="succeeded",
            output={
                "query": request.goal,
                "topic": project_id,
                "document_count": len(evidence),
                "summary": f"Retrieved {len(evidence)} authorized document(s) for '{project_id}'.",
            },
            evidence=evidence,
            warnings=[],
        )


class KnowledgeAnalysisAgent:
    """Synthesizes validated retrieval evidence into an evidence-backed enterprise answer."""

    def __init__(self) -> None:
        self._metadata = AgentMetadata(
            agent_id="knowledge_analysis",
            name="KEEP Knowledge Analysis Agent",
            version="1.0.0",
            description="Synthesizes retrieved tenant evidence into structured executive findings.",
            capabilities=[
                AgentCapability(
                    name="knowledge.analyze",
                    description="Analyze retrieved evidence and produce structured findings.",
                    access="read",
                )
            ],
            tags=["phase-4.3", "analysis", "orchestration"],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        if request.input.get("force_fail") is True:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message="Simulated analysis agent failure.",
                retryable=False,
            )

        raw_evidence = list(request.input.get("evidence") or [])
        topic = str(request.input.get("topic") or "enterprise-core")
        citations = [
            ev if isinstance(ev, EvidenceReference) else EvidenceReference.model_validate(ev)
            for ev in raw_evidence
        ]
        findings = [
            f"Grounded finding from '{ev.title or ev.source_id}': {(ev.excerpt or '')[:140]}"
            for ev in citations
        ]
        if not findings:
            findings = [f"Analyzed goal '{request.goal}' for topic '{topic}'."]

        return AgentResult(
            status="succeeded",
            output={
                "summary": f"Synthesized {len(citations)} authorized source(s) for '{request.goal}'.",
                "key_findings": findings,
                "confidence": 0.93 if citations else 0.5,
                "sources_used": len(citations),
                "tenant_id": context.tenant_id,
            },
            evidence=citations,
            warnings=[],
        )


class DecisionExtractionAgent:
    """Parallel branch specialist extracting recorded decisions and accountable owners."""

    def __init__(self) -> None:
        self._metadata = AgentMetadata(
            agent_id="decision_extractor",
            name="KEEP Decision Extraction Agent",
            version="1.0.0",
            description="Extracts formal architectural and project decisions with owners from retrieved evidence.",
            capabilities=[
                AgentCapability(
                    name="knowledge.decisions",
                    description="Extract decisions and accountable owners from enterprise documents.",
                    access="read",
                )
            ],
            tags=["phase-4.3", "parallel", "decisions"],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        if request.input.get("force_fail_decisions") is True:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message="Simulated decision extraction branch failure.",
                retryable=False,
            )

        raw_evidence = list(request.input.get("evidence") or [])
        citations = [
            ev if isinstance(ev, EvidenceReference) else EvidenceReference.model_validate(ev)
            for ev in raw_evidence
        ]
        topic = str(request.input.get("topic") or "enterprise-core")
        decisions: list[dict[str, Any]] = [
            {
                "decision_id": f"dec_{topic}_01",
                "title": f"Enforce Phase 4.2 AgentRuntime boundary for {topic}",
                "owner": "Platform Engineering Lead",
                "status": "APPROVED",
                "source_id": citations[0].source_id if citations else "internal",
            }
        ]
        return AgentResult(
            status="succeeded",
            output={
                "branch_name": "decisions",
                "summary": f"Extracted {len(decisions)} decision(s) for '{topic}'.",
                "items": decisions,
                "confidence": 0.92,
                "tenant_id": context.tenant_id,
            },
            evidence=citations[:1],
            warnings=[],
        )


class RiskAnalysisAgent:
    """Parallel branch specialist identifying blockers, delivery risks, and mitigations."""

    def __init__(self) -> None:
        self._metadata = AgentMetadata(
            agent_id="risk_analyzer",
            name="KEEP Risk Analysis Agent",
            version="1.0.0",
            description="Identifies operational blockers, security risks, and mitigations from retrieved evidence.",
            capabilities=[
                AgentCapability(
                    name="knowledge.risks",
                    description="Identify project risks and blockers from enterprise documents.",
                    access="read",
                )
            ],
            tags=["phase-4.3", "parallel", "risks"],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        if request.input.get("force_fail_risks") is True:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message="Simulated optional risk analyzer failure.",
                retryable=False,
            )

        raw_evidence = list(request.input.get("evidence") or [])
        citations = [
            ev if isinstance(ev, EvidenceReference) else EvidenceReference.model_validate(ev)
            for ev in raw_evidence
        ]
        topic = str(request.input.get("topic") or "enterprise-core")
        risks: list[dict[str, Any]] = [
            {
                "risk_id": f"risk_{topic}_01",
                "severity": "MEDIUM",
                "description": f"Upstream provider latency during parallel synthesis for {topic}",
                "mitigation": "Enforce bounded per-agent timeouts and partial-success fallback.",
                "source_id": citations[-1].source_id if citations else "internal",
            }
        ]
        return AgentResult(
            status="succeeded",
            output={
                "branch_name": "risks",
                "summary": f"Identified {len(risks)} risk(s) for '{topic}'.",
                "items": risks,
                "confidence": 0.90,
                "tenant_id": context.tenant_id,
            },
            evidence=citations[-1:] if citations else [],
            warnings=[],
        )

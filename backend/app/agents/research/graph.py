"""KEEP Phase 4.5 — Controlled Research Graph (`KeepStateGraph` Pipeline).

Orchestrates the bounded, evidence-first research workflow inside KEEP's
LangGraph-compatible `KeepStateGraph`:

    START ──► retrieve ──► [evidence found?]
                               ├── No  ──► insufficient_evidence ──► END
                               └── Yes ──► synthesize ──► validate_quality
                                                              ├── Valid ──► finalize ──► END
                                                              ├── Retry (<1) ──► correct_once ──► validate_quality
                                                              └── Exhausted ──► finalize_partial ──► END

Owner: Member 4 (Research Graph, Persistence, API & QA)
Specification: devdocs/p4/p4.5.txt (Sections 2, 5, 6, 7)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.adapters.keep_services import KeepKnowledgeAdapter
from backend.app.agents.adapters.langgraph_orchestrator import (
    END,
    START,
    CompiledKeepWorkflowGraph,
    KeepStateGraph,
)
from backend.app.agents.contracts import AgentContext
from backend.app.agents.research.agent import MAX_CORRECTION_ATTEMPTS, KeepResearchAgent
from backend.app.agents.research.contracts import (
    EvidenceItem,
    QualityCheckResult,
    ResearchQualityInterface,
    ResearchReport,
    ResearchRequest,
    ResearchRetrievalInterface,
    ResearchStatus,
    ResearchSynthesisInterface,
    RetrievalOutcome,
    SynthesisDraft,
)
from backend.app.agents.research.quality import ResearchQualityValidator
from backend.app.agents.research.retrieval import KeepResearchRetrievalService
from backend.app.agents.research.source_registry import AuthorizedSourceCatalog
from backend.app.agents.research.synthesis import KeepResearchSynthesisService
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)


def build_research_graph(
    *,
    retrieval: ResearchRetrievalInterface,
    synthesis: ResearchSynthesisInterface,
    quality: ResearchQualityInterface,
    max_correction_attempts: int = MAX_CORRECTION_ATTEMPTS,
) -> CompiledKeepWorkflowGraph:
    """Compiles KEEP's bounded evidence-first research workflow graph."""
    max_retries = max(0, min(max_correction_attempts, 2))

    async def node_retrieve(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        outcome = await retrieval.retrieve_evidence(req, context)
        return {
            "retrieval_outcome": outcome.model_dump(mode="json"),
            "evidence": [e.model_dump(mode="json") for e in outcome.evidence],
            "warnings": list(outcome.warnings),
            "correction_attempts": 0,
        }

    def route_after_retrieve(state: dict[str, Any]) -> str:
        evidence = state.get("evidence") or []
        return "synthesize" if len(evidence) > 0 else "insufficient_evidence"

    async def node_insufficient(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        outcome = RetrievalOutcome.model_validate(state["retrieval_outcome"])
        report = ResearchReport(
            research_id=req.research_id,
            question=req.question,
            scope=req.scope,
            required_output=req.required_output,
            status=ResearchStatus.INSUFFICIENT_EVIDENCE,
            summary=(
                "Insufficient authorized internal evidence was retrieved from KEEP knowledge "
                "sources to answer this research question without speculation."
            ),
            findings=[],
            evidence=[],
            contradictions=[],
            unresolved_questions=[
                f"No authorized KEEP records matched the question: '{req.question}'."
            ],
            follow_up_suggestions=[
                "Broaden the research scope or verify that relevant documents are indexed in your tenant."
            ],
            warnings=list(outcome.warnings),
            correction_attempts=0,
            sources_retrieved=outcome.sources_retrieved,
            sources_retained=0,
            retrieval_latency_ms=outcome.retrieval_latency_ms,
            synthesis_latency_ms=0,
            correlation_id=context.correlation_id,
            completed_at=datetime.now(UTC),
        )
        return {"report": report.model_dump(mode="json")}

    async def node_synthesize(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        evidence = [EvidenceItem.model_validate(e) for e in state["evidence"]]
        draft = await synthesis.synthesize(req, evidence, context)
        return {"draft": draft.model_dump(mode="json")}

    async def node_validate(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        evidence = [EvidenceItem.model_validate(e) for e in state["evidence"]]
        draft = SynthesisDraft.model_validate(state["draft"])
        result = quality.validate(req, draft, evidence)
        return {"quality": result.model_dump(mode="json")}

    def route_after_validate(state: dict[str, Any]) -> str:
        q = QualityCheckResult.model_validate(state["quality"])
        if q.is_valid:
            return "finalize"
        attempts = int(state.get("correction_attempts", 0))
        if attempts < max_retries:
            return "correct_once"
        return "finalize_partial"

    async def node_correct_once(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        evidence = [EvidenceItem.model_validate(e) for e in state["evidence"]]
        draft = SynthesisDraft.model_validate(state["draft"])
        q = QualityCheckResult.model_validate(state["quality"])
        repaired = await synthesis.correct_findings(req, draft, evidence, q.issues, context)
        return {
            "draft": repaired.model_dump(mode="json"),
            "correction_attempts": int(state.get("correction_attempts", 0)) + 1,
        }

    async def node_finalize(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        outcome = RetrievalOutcome.model_validate(state["retrieval_outcome"])
        evidence = [EvidenceItem.model_validate(e) for e in state["evidence"]]
        draft = SynthesisDraft.model_validate(state["draft"])
        q = QualityCheckResult.model_validate(state["quality"])

        all_warnings = list(dict.fromkeys(list(outcome.warnings) + list(q.warnings)))
        unresolved = list(
            dict.fromkeys(draft.unresolved_questions + q.recommended_unresolved_questions)
        )
        report = ResearchReport(
            research_id=req.research_id,
            question=req.question,
            scope=req.scope,
            required_output=req.required_output,
            status=ResearchStatus.COMPLETED,
            summary=draft.summary,
            findings=draft.findings,
            evidence=evidence,
            contradictions=draft.contradictions,
            unresolved_questions=unresolved,
            follow_up_suggestions=draft.follow_up_suggestions,
            warnings=all_warnings,
            correction_attempts=int(state.get("correction_attempts", 0)),
            sources_retrieved=outcome.sources_retrieved,
            sources_retained=len(evidence),
            retrieval_latency_ms=outcome.retrieval_latency_ms,
            synthesis_latency_ms=draft.synthesis_latency_ms,
            correlation_id=context.correlation_id,
            completed_at=datetime.now(UTC),
        )
        return {"report": report.model_dump(mode="json")}

    async def node_finalize_partial(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        req = ResearchRequest.model_validate(state["request"])
        outcome = RetrievalOutcome.model_validate(state["retrieval_outcome"])
        evidence = [EvidenceItem.model_validate(e) for e in state["evidence"]]
        draft = SynthesisDraft.model_validate(state["draft"])
        q = QualityCheckResult.model_validate(state["quality"])

        valid_ids = {item.evidence_id for item in evidence}
        safe_findings = []
        for finding in draft.findings:
            cleaned = [eid for eid in finding.evidence_ids if eid in valid_ids]
            if finding.claim_type == "factual" and not cleaned:
                continue
            safe_findings.append(finding.model_copy(update={"evidence_ids": cleaned}))

        status_val = (
            ResearchStatus.PARTIAL if safe_findings else ResearchStatus.INSUFFICIENT_EVIDENCE
        )
        all_warnings = list(dict.fromkeys(list(outcome.warnings) + list(q.warnings) + list(q.issues)))
        unresolved = list(dict.fromkeys(draft.unresolved_questions + q.issues))

        report = ResearchReport(
            research_id=req.research_id,
            question=req.question,
            scope=req.scope,
            required_output=req.required_output,
            status=status_val,
            summary=draft.summary,
            findings=safe_findings,
            evidence=evidence,
            contradictions=draft.contradictions,
            unresolved_questions=unresolved,
            follow_up_suggestions=draft.follow_up_suggestions,
            warnings=all_warnings,
            correction_attempts=int(state.get("correction_attempts", 0)),
            sources_retrieved=outcome.sources_retrieved,
            sources_retained=len(evidence),
            retrieval_latency_ms=outcome.retrieval_latency_ms,
            synthesis_latency_ms=draft.synthesis_latency_ms,
            correlation_id=context.correlation_id,
            completed_at=datetime.now(UTC),
        )
        return {"report": report.model_dump(mode="json")}

    graph = KeepStateGraph()
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("insufficient_evidence", node_insufficient)
    graph.add_node("synthesize", node_synthesize)
    graph.add_node("validate_quality", node_validate)
    graph.add_node("correct_once", node_correct_once)
    graph.add_node("finalize", node_finalize)
    graph.add_node("finalize_partial", node_finalize_partial)

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "synthesize": "synthesize",
            "insufficient_evidence": "insufficient_evidence",
        },
    )
    graph.add_edge("insufficient_evidence", END)
    graph.add_edge("synthesize", "validate_quality")
    graph.add_conditional_edges(
        "validate_quality",
        route_after_validate,
        {
            "finalize": "finalize",
            "correct_once": "correct_once",
            "finalize_partial": "finalize_partial",
        },
    )
    graph.add_edge("correct_once", "validate_quality")
    graph.add_edge("finalize", END)
    graph.add_edge("finalize_partial", END)

    return graph.compile()


def build_default_research_agent(
    *,
    knowledge_adapter: KeepKnowledgeAdapter | None = None,
    source_catalog: AuthorizedSourceCatalog | None = None,
    retrieval: ResearchRetrievalInterface | None = None,
    synthesis: ResearchSynthesisInterface | None = None,
    quality: ResearchQualityInterface | None = None,
    policy: AgentPolicyInterface | None = None,
    max_correction_attempts: int = MAX_CORRECTION_ATTEMPTS,
) -> KeepResearchAgent:
    """Constructs KEEP's production `KeepResearchAgent` wired to the compiled research graph."""
    sec_policy = policy or KeepAgentPolicyEngine()
    retrieval_svc = retrieval or KeepResearchRetrievalService(
        knowledge_adapter=knowledge_adapter,
        source_catalog=source_catalog,
        policy=sec_policy,
    )
    synthesis_svc = synthesis or KeepResearchSynthesisService()
    quality_svc = quality or ResearchQualityValidator()

    compiled_graph = build_research_graph(
        retrieval=retrieval_svc,
        synthesis=synthesis_svc,
        quality=quality_svc,
        max_correction_attempts=max_correction_attempts,
    )

    async def _run_graph(request: ResearchRequest, context: AgentContext) -> ResearchReport:
        final_state = await compiled_graph.arun(
            {"request": request.model_dump(mode="json")},
            context=context,
        )
        return ResearchReport.model_validate(final_state["report"])

    return KeepResearchAgent(
        retrieval=retrieval_svc,
        synthesis=synthesis_svc,
        quality=quality_svc,
        policy=sec_policy,
        runner_fn=_run_graph,
        max_correction_attempts=max_correction_attempts,
    )

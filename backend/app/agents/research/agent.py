"""KEEP Phase 4.5 — KeepResearchAgent (BaseAgent Implementation).

Implements KEEP's canonical Phase 4.1 `BaseAgent` Protocol (`agent_id="research_agent"`)
so research investigations execute seamlessly through Phase 4.2 `AgentRuntime`,
Phase 4.3 `KeepOrchestrationService`, and Phase 4.4 `KeepPlanningService`.

Owner: Member 1 (Research Agent Core)
Specification: devdocs/p4/p4.5.txt (Sections 3, 4.1, 4.2, 5, 7)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentErrorCode,
    AgentLayerError,
    ResearchRetrievalUnavailableError,
)
from backend.app.agents.metadata import AgentCapability, AgentMetadata
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
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)

MAX_CORRECTION_ATTEMPTS = 1

ResearchRunnerFn = Callable[
    [ResearchRequest, AgentContext],
    Awaitable[ResearchReport],
]


class _NoOpRetrieval:
    """Fallback empty retrieval implementation used when no retrieval service is injected."""

    async def retrieve_evidence(
        self,
        request: ResearchRequest,
        context: AgentContext,
    ) -> RetrievalOutcome:
        return RetrievalOutcome(evidence=[], sources_retrieved=0, sources_retained=0)


class _BasicSynthesis:
    """Minimal grounded synthesis fallback used in Stage 1 core unit tests."""

    async def synthesize(
        self,
        request: ResearchRequest,
        evidence: list[EvidenceItem],
        context: AgentContext,
    ) -> SynthesisDraft:
        if not evidence:
            return SynthesisDraft(
                summary="Insufficient authorized evidence was found to answer this question.",
                findings=[],
                unresolved_questions=[f"No authorized KEEP records matched: {request.question}"],
            )
        from backend.app.agents.research.contracts import ResearchFinding

        first = evidence[0]
        return SynthesisDraft(
            summary=f"Synthesized {len(evidence)} authorized evidence passage(s) for '{request.question}'.",
            findings=[
                ResearchFinding(
                    finding_id="f_01",
                    claim=first.passage[:320],
                    claim_type="factual",
                    evidence_ids=[first.evidence_id],
                    confidence="medium" if len(evidence) > 1 else "low",
                    limitations=[] if len(evidence) > 1 else ["Single supporting source only."],
                )
            ],
            unresolved_questions=[],
            follow_up_suggestions=["Inspect full evidence provenance for detailed context."],
        )

    async def correct_findings(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
        quality_issues: list[str],
        context: AgentContext,
    ) -> SynthesisDraft:
        valid_ids = {item.evidence_id for item in evidence}
        repaired = []
        for finding in draft.findings:
            cleaned_ids = [eid for eid in finding.evidence_ids if eid in valid_ids]
            if finding.claim_type == "factual" and not cleaned_ids:
                continue
            repaired.append(finding.model_copy(update={"evidence_ids": cleaned_ids}))
        return draft.model_copy(update={"findings": repaired})


class _BasicQuality:
    """Minimal citation integrity check fallback used before Member 3's full validator."""

    def validate(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
    ) -> QualityCheckResult:
        valid_ids = {item.evidence_id for item in evidence}
        invalid_citations: list[str] = []
        unsupported: list[str] = []
        issues: list[str] = []
        for finding in draft.findings:
            for eid in finding.evidence_ids:
                if eid not in valid_ids:
                    invalid_citations.append(eid)
                    issues.append(f"Finding '{finding.finding_id}' cites unknown evidence_id '{eid}'.")
            if finding.claim_type == "factual" and not [
                eid for eid in finding.evidence_ids if eid in valid_ids
            ]:
                unsupported.append(finding.finding_id)
                issues.append(
                    f"Factual finding '{finding.finding_id}' has no valid supporting evidence_id."
                )
        return QualityCheckResult(
            is_valid=len(issues) == 0,
            invalid_citations=invalid_citations,
            unsupported_findings=unsupported,
            issues=issues,
        )


def build_research_agent_metadata() -> AgentMetadata:
    """Returns canonical Phase 4.5 AgentMetadata for KEEP's registered Research Agent."""
    return AgentMetadata(
        agent_id="research_agent",
        name="KEEP Research Agent",
        version="1.0.0",
        description=(
            "Conducts multi-source investigative research across authorized KEEP knowledge, "
            "synthesizes grounded findings with traceable citations, surfaces contradictions, "
            "and reports evidence gaps transparently."
        ),
        capabilities=[
            AgentCapability(
                name="knowledge.research",
                description="Conduct multi-document investigative research across authorized KEEP sources.",
                access="read",
            ),
            AgentCapability(
                name="evidence.synthesis",
                description="Synthesize cross-source findings with confidence levels and contradiction reporting.",
                access="read",
            ),
            AgentCapability(
                name="citation.validation",
                description="Verify that factual findings map strictly to retrieved authorized evidence IDs.",
                access="read",
            ),
        ],
        enabled=True,
        tags=["phase-4.5", "research", "evidence", "citations", "read-only"],
    )


class KeepResearchAgent:
    """KEEP's first specialized investigative agent implementing `BaseAgent`."""

    def __init__(
        self,
        *,
        retrieval: ResearchRetrievalInterface | None = None,
        synthesis: ResearchSynthesisInterface | None = None,
        quality: ResearchQualityInterface | None = None,
        policy: AgentPolicyInterface | None = None,
        runner_fn: ResearchRunnerFn | None = None,
        max_correction_attempts: int = MAX_CORRECTION_ATTEMPTS,
    ) -> None:
        self._metadata = build_research_agent_metadata()
        self._retrieval: ResearchRetrievalInterface = retrieval or _NoOpRetrieval()
        self._synthesis: ResearchSynthesisInterface = synthesis or _BasicSynthesis()
        self._quality: ResearchQualityInterface = quality or _BasicQuality()
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()
        self._runner_fn = runner_fn
        self._max_correction_attempts = max(0, min(max_correction_attempts, 2))

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    def bind_runner(self, runner_fn: ResearchRunnerFn) -> None:
        """Attaches an orchestrated research graph runner (e.g., Phase 4.5 LangGraph pipeline)."""
        self._runner_fn = runner_fn

    def _parse_research_request(self, request: AgentRequest) -> ResearchRequest:
        """Converts an `AgentRequest` into a validated `ResearchRequest`."""
        payload = request.input or {}
        question = str(payload.get("question") or request.goal).strip()
        scope = payload.get("scope")
        max_sources_raw = payload.get("max_sources", 12)
        try:
            max_sources = int(max_sources_raw)
        except (TypeError, ValueError):
            max_sources = 12
        max_sources = max(1, min(30, max_sources))

        required_output = str(payload.get("required_output") or "detailed_report")
        if required_output not in ("summary", "comparison", "detailed_report"):
            required_output = "detailed_report"

        raw_filters = payload.get("filters")
        filters: dict[str, Any] = dict(raw_filters) if isinstance(raw_filters, dict) else {}

        kwargs: dict[str, Any] = {
            "question": question,
            "scope": str(scope).strip() if isinstance(scope, str) and scope.strip() else None,
            "max_sources": max_sources,
            "required_output": required_output,
            "filters": filters,
            "plan_id": payload.get("plan_id"),
            "workflow_execution_id": payload.get("workflow_execution_id"),
            "agent_execution_id": payload.get("agent_execution_id"),
        }
        if isinstance(payload.get("research_id"), str) and payload["research_id"].strip():
            kwargs["research_id"] = payload["research_id"].strip()
        return ResearchRequest(**kwargs)

    async def run_research(
        self,
        research_request: ResearchRequest,
        context: AgentContext,
    ) -> ResearchReport:
        """Executes the evidence-first research flow (delegates to graph runner when bound)."""
        self._policy.verify_trusted_context(context)
        if self._runner_fn is not None:
            return await self._runner_fn(research_request, context)

        retrieval_outcome = await self._retrieval.retrieve_evidence(research_request, context)
        evidence = retrieval_outcome.evidence

        if not evidence:
            return ResearchReport(
                research_id=research_request.research_id,
                question=research_request.question,
                scope=research_request.scope,
                required_output=research_request.required_output,
                status=ResearchStatus.INSUFFICIENT_EVIDENCE,
                summary=(
                    "Insufficient authorized evidence was retrieved from KEEP knowledge sources "
                    "to answer this research question without speculation."
                ),
                findings=[],
                evidence=[],
                contradictions=[],
                unresolved_questions=[
                    f"No authorized KEEP sources contained evidence for: '{research_request.question}'."
                ],
                follow_up_suggestions=[
                    "Broaden the investigation scope or verify that relevant documents are indexed in your tenant."
                ],
                warnings=list(retrieval_outcome.warnings),
                correction_attempts=0,
                sources_retrieved=retrieval_outcome.sources_retrieved,
                sources_retained=0,
                retrieval_latency_ms=retrieval_outcome.retrieval_latency_ms,
                synthesis_latency_ms=0,
                correlation_id=context.correlation_id,
                completed_at=datetime.now(UTC),
            )

        draft = await self._synthesis.synthesize(research_request, evidence, context)
        quality_result = self._quality.validate(research_request, draft, evidence)

        correction_attempts = 0
        warnings = list(retrieval_outcome.warnings) + list(quality_result.warnings)

        while not quality_result.is_valid and correction_attempts < self._max_correction_attempts:
            correction_attempts += 1
            draft = await self._synthesis.correct_findings(
                research_request,
                draft,
                evidence,
                quality_result.issues,
                context,
            )
            quality_result = self._quality.validate(research_request, draft, evidence)
            warnings.extend(quality_result.warnings)

        if not quality_result.is_valid:
            # Strip any invalid citations deterministically before returning a qualified partial report
            valid_ids = {item.evidence_id for item in evidence}
            safe_findings = []
            for finding in draft.findings:
                valid_refs = [eid for eid in finding.evidence_ids if eid in valid_ids]
                if finding.claim_type == "factual" and not valid_refs:
                    continue
                safe_findings.append(finding.model_copy(update={"evidence_ids": valid_refs}))
            unresolved = list(dict.fromkeys(draft.unresolved_questions + quality_result.issues))
            return ResearchReport(
                research_id=research_request.research_id,
                question=research_request.question,
                scope=research_request.scope,
                required_output=research_request.required_output,
                status=ResearchStatus.PARTIAL if safe_findings else ResearchStatus.INSUFFICIENT_EVIDENCE,
                summary=draft.summary,
                findings=safe_findings,
                evidence=evidence,
                contradictions=draft.contradictions,
                unresolved_questions=unresolved,
                follow_up_suggestions=draft.follow_up_suggestions,
                warnings=list(dict.fromkeys(warnings + quality_result.issues)),
                correction_attempts=correction_attempts,
                sources_retrieved=retrieval_outcome.sources_retrieved,
                sources_retained=len(evidence),
                retrieval_latency_ms=retrieval_outcome.retrieval_latency_ms,
                synthesis_latency_ms=draft.synthesis_latency_ms,
                correlation_id=context.correlation_id,
                completed_at=datetime.now(UTC),
            )

        unresolved = list(
            dict.fromkeys(draft.unresolved_questions + quality_result.recommended_unresolved_questions)
        )
        return ResearchReport(
            research_id=research_request.research_id,
            question=research_request.question,
            scope=research_request.scope,
            required_output=research_request.required_output,
            status=ResearchStatus.COMPLETED,
            summary=draft.summary,
            findings=draft.findings,
            evidence=evidence,
            contradictions=draft.contradictions,
            unresolved_questions=unresolved,
            follow_up_suggestions=draft.follow_up_suggestions,
            warnings=list(dict.fromkeys(warnings)),
            correction_attempts=correction_attempts,
            sources_retrieved=retrieval_outcome.sources_retrieved,
            sources_retained=len(evidence),
            retrieval_latency_ms=retrieval_outcome.retrieval_latency_ms,
            synthesis_latency_ms=draft.synthesis_latency_ms,
            correlation_id=context.correlation_id,
            completed_at=datetime.now(UTC),
        )

    async def invoke(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Executes research via the canonical Phase 4.1 `BaseAgent` contract."""
        try:
            self._policy.authorize_invocation(self._metadata, request, context)
            research_request = self._parse_research_request(request)
            report = await self.run_research(research_request, context)
        except ResearchRetrievalUnavailableError as exc:
            return AgentResult.failure(
                code=exc.code,
                message=str(exc),
                retryable=True,
                details=exc.details,
            )
        except AgentLayerError as exc:
            return AgentResult.failure(
                code=exc.code,
                message=str(exc),
                retryable=exc.retryable,
                details=exc.details,
            )
        except Exception as exc:  # noqa: BLE001 - convert unexpected failure into sanitized AgentResult
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message=f"Research agent execution failed: {exc}",
            )

        evidence_refs = [
            item.to_agent_evidence_reference(tenant_id=context.tenant_id)
            for item in report.evidence
        ]
        return AgentResult(
            status="succeeded",
            output={
                "research_id": report.research_id,
                "status": report.status.value,
                "summary": report.summary,
                "report": report.model_dump(mode="json"),
                "findings_count": len(report.findings),
                "evidence_count": len(report.evidence),
                "contradictions_count": len(report.contradictions),
            },
            evidence=evidence_refs,
            warnings=report.warnings,
        )

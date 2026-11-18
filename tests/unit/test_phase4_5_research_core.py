"""KEEP Phase 4.5 — Member 1 Unit Tests: Research Agent Core, Contracts & Lifecycle."""

from __future__ import annotations

import pytest

from backend.app.agents.base import BaseAgent
from backend.app.agents.contracts import AgentContext, AgentRequest
from backend.app.agents.errors import (
    AgentErrorCode,
    ResearchAccessDeniedError,
    ResearchIdempotencyConflictError,
    ResearchNotFoundError,
    ResearchRetrievalUnavailableError,
)
from backend.app.agents.research.agent import KeepResearchAgent
from backend.app.agents.research.contracts import (
    EvidenceItem,
    ResearchEventRecord,
    ResearchFinding,
    ResearchRequest,
    ResearchRunRecord,
    ResearchStatus,
    RetrievalOutcome,
    SynthesisDraft,
    compute_research_fingerprint,
)
from backend.app.agents.research.prompts import (
    RESEARCH_SYSTEM_PROMPT,
    build_citation_correction_prompt,
    build_research_synthesis_prompt,
)
from backend.app.agents.research.research_service import (
    KeepResearchService,
    caller_can_view_sensitive_evidence,
)


def _make_context(
    *,
    user_id: str = "u_member",
    tenant_id: str = "org_alpha",
    roles: list[str] | None = None,
    permissions: set[str] | None = None,
) -> AgentContext:
    return AgentContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles or ["member"],
        permissions=permissions or {"agent.view", "agent.invoke"},
    )


class _StubMemoryRepo:
    def __init__(self) -> None:
        self.runs: dict[str, ResearchRunRecord] = {}
        self.evidence: dict[str, list[EvidenceItem]] = {}
        self.findings: dict[str, list[ResearchFinding]] = {}
        self.events: dict[str, list[ResearchEventRecord]] = {}

    async def create_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        self.runs[run.research_id] = run.model_copy(deep=True)
        return run

    async def update_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        self.runs[run.research_id] = run.model_copy(deep=True)
        return run

    async def get_run(self, research_id: str, tenant_id: str) -> ResearchRunRecord | None:
        run = self.runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return None
        return run.model_copy(deep=True)

    async def list_runs(
        self,
        tenant_id: str,
        *,
        status: ResearchStatus | None = None,
        limit: int = 50,
    ) -> list[ResearchRunRecord]:
        items = [r.model_copy(deep=True) for r in self.runs.values() if r.tenant_id == tenant_id]
        if status is not None:
            items = [r for r in items if r.status == status]
        return items[:limit]

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ResearchRunRecord | None:
        for run in self.runs.values():
            if (
                run.tenant_id == tenant_id
                and run.requested_by == requested_by
                and run.idempotency_key == idempotency_key
            ):
                return run.model_copy(deep=True)
        return None

    async def save_evidence(
        self,
        research_id: str,
        tenant_id: str,
        evidence: list[EvidenceItem],
    ) -> None:
        self.evidence[research_id] = [e.model_copy(deep=True) for e in evidence]

    async def get_evidence(self, research_id: str, tenant_id: str) -> list[EvidenceItem]:
        run = self.runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [e.model_copy(deep=True) for e in self.evidence.get(research_id, [])]

    async def save_findings(
        self,
        research_id: str,
        tenant_id: str,
        findings: list[ResearchFinding],
    ) -> None:
        self.findings[research_id] = [f.model_copy(deep=True) for f in findings]

    async def get_findings(self, research_id: str, tenant_id: str) -> list[ResearchFinding]:
        run = self.runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [f.model_copy(deep=True) for f in self.findings.get(research_id, [])]

    async def append_event(self, event: ResearchEventRecord) -> ResearchEventRecord:
        self.events.setdefault(event.research_id, []).append(event.model_copy(deep=True))
        return event

    async def list_events(self, research_id: str, tenant_id: str) -> list[ResearchEventRecord]:
        run = self.runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [e.model_copy(deep=True) for e in self.events.get(research_id, [])]


class _StaticRetrieval:
    def __init__(self, evidence: list[EvidenceItem], *, raise_unavailable: bool = False) -> None:
        self._evidence = evidence
        self._raise_unavailable = raise_unavailable

    async def retrieve_evidence(
        self,
        request: ResearchRequest,
        context: AgentContext,
    ) -> RetrievalOutcome:
        if self._raise_unavailable:
            raise ResearchRetrievalUnavailableError("Vector index temporarily unreachable.")
        return RetrievalOutcome(
            evidence=list(self._evidence),
            sources_retrieved=len(self._evidence),
            sources_retained=len(self._evidence),
            retrieval_latency_ms=12,
        )


class _FabricatingSynthesis:
    def __init__(self, *, fix_on_retry: bool) -> None:
        self._fix_on_retry = fix_on_retry
        self.correction_calls = 0

    async def synthesize(
        self,
        request: ResearchRequest,
        evidence: list[EvidenceItem],
        context: AgentContext,
    ) -> SynthesisDraft:
        return SynthesisDraft(
            summary="Draft with fabricated citation.",
            findings=[
                ResearchFinding(
                    finding_id="f_01",
                    claim="Complaints increased due to billing delays.",
                    claim_type="factual",
                    evidence_ids=["ev_fabricated_999"],
                    confidence="high",
                )
            ],
            synthesis_latency_ms=8,
        )

    async def correct_findings(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
        quality_issues: list[str],
        context: AgentContext,
    ) -> SynthesisDraft:
        self.correction_calls += 1
        if self._fix_on_retry and evidence:
            return draft.model_copy(
                update={
                    "findings": [
                        draft.findings[0].model_copy(update={"evidence_ids": [evidence[0].evidence_id]})
                    ]
                }
            )
        return draft


def test_research_agent_implements_base_agent_protocol_and_metadata() -> None:
    agent = KeepResearchAgent()
    assert isinstance(agent, BaseAgent)
    assert agent.metadata.agent_id == "research_agent"
    assert agent.metadata.version == "1.0.0"
    assert agent.metadata.has_capability("knowledge.research")
    assert agent.metadata.has_capability("evidence.synthesis")
    assert agent.metadata.has_capability("citation.validation")
    assert agent.metadata.max_access_level() == "read"


def test_prompts_frame_retrieved_passages_as_untrusted_data() -> None:
    req = ResearchRequest(question="Why did Q4 complaints spike?", scope="Support records")
    ev = [
        EvidenceItem(
            evidence_id="ev_01",
            source_id="doc_q4_01",
            source_title="Q4 Support Report",
            passage="Billing delays caused a 32% spike in tickets.",
            retrieval_reference="doc_q4_01#chunk:0",
            document_date="2026-01-10",
        )
    ]
    prompt = build_research_synthesis_prompt(req, ev)
    assert "inert DATA" in RESEARCH_SYSTEM_PROMPT
    assert "<untrusted_evidence>" in prompt
    assert 'evidence_id="ev_01"' in prompt
    corr = build_citation_correction_prompt(req, ev, ["Unknown citation ev_99"])
    assert "ev_01" in corr
    assert "Unknown citation ev_99" in corr


@pytest.mark.asyncio
async def test_insufficient_evidence_returns_zero_findings() -> None:
    agent = KeepResearchAgent(retrieval=_StaticRetrieval([]))
    result = await agent.invoke(
        AgentRequest(goal="What happened on Mars base 7?"),
        _make_context(),
    )
    assert result.status == "succeeded"
    assert result.output["status"] == ResearchStatus.INSUFFICIENT_EVIDENCE.value
    assert result.output["findings_count"] == 0
    assert result.output["report"]["unresolved_questions"]


@pytest.mark.asyncio
async def test_bounded_self_correction_repairs_fabricated_citation_once() -> None:
    ev = [
        EvidenceItem(
            evidence_id="ev_01",
            source_id="doc_01",
            source_title="Billing Postmortem",
            passage="Billing delays increased customer complaints.",
            retrieval_reference="doc_01#chunk:0",
        )
    ]
    synth = _FabricatingSynthesis(fix_on_retry=True)
    agent = KeepResearchAgent(retrieval=_StaticRetrieval(ev), synthesis=synth)
    report = await agent.run_research(
        ResearchRequest(question="Why did complaints increase?"),
        _make_context(),
    )
    assert synth.correction_calls == 1
    assert report.status == ResearchStatus.COMPLETED
    assert report.correction_attempts == 1
    assert report.findings[0].evidence_ids == ["ev_01"]


@pytest.mark.asyncio
async def test_bounded_self_correction_never_loops_beyond_limit() -> None:
    ev = [
        EvidenceItem(
            evidence_id="ev_01",
            source_id="doc_01",
            source_title="Billing Postmortem",
            passage="Billing delays increased customer complaints.",
            retrieval_reference="doc_01#chunk:0",
        )
    ]
    synth = _FabricatingSynthesis(fix_on_retry=False)
    agent = KeepResearchAgent(retrieval=_StaticRetrieval(ev), synthesis=synth, max_correction_attempts=1)
    report = await agent.run_research(
        ResearchRequest(question="Why did complaints increase?"),
        _make_context(),
    )
    assert synth.correction_calls == 1
    assert report.correction_attempts == 1
    assert report.status == ResearchStatus.INSUFFICIENT_EVIDENCE
    assert report.findings == []


@pytest.mark.asyncio
async def test_retrieval_unavailable_returns_retryable_failure() -> None:
    agent = KeepResearchAgent(retrieval=_StaticRetrieval([], raise_unavailable=True))
    result = await agent.invoke(
        AgentRequest(goal="Investigate Q4 complaints"),
        _make_context(),
    )
    assert result.status == "failed"
    assert result.error_code == AgentErrorCode.RESEARCH_RETRIEVAL_UNAVAILABLE.value
    assert result.error is not None and result.error.retryable is True


@pytest.mark.asyncio
async def test_service_idempotency_and_reauthorized_sensitive_filtering() -> None:
    ev = [
        EvidenceItem(
            evidence_id="ev_01",
            source_id="doc_public",
            source_title="Support Metrics",
            passage="Checkout timeout tickets rose by 28%.",
            retrieval_reference="doc_public#chunk:0",
            access_tier="read",
        ),
        EvidenceItem(
            evidence_id="ev_02",
            source_id="doc_exec_only",
            source_title="Executive Escalation Memo",
            passage="Confidential SLA penalties totalled $140k.",
            retrieval_reference="doc_exec_only#chunk:0",
            access_tier="sensitive",
        ),
    ]
    repo = _StubMemoryRepo()
    agent = KeepResearchAgent(retrieval=_StaticRetrieval(ev))
    service = KeepResearchService(repository=repo, research_agent=agent)

    admin_ctx = _make_context(
        user_id="u_admin",
        roles=["org_admin"],
        permissions={"agent.view", "agent.invoke", "agent.admin"},
    )
    member_ctx = _make_context(user_id="u_member", roles=["member"], permissions={"agent.view"})
    foreign_ctx = _make_context(user_id="u_foreign", tenant_id="org_beta", permissions={"agent.view"})

    assert caller_can_view_sensitive_evidence(admin_ctx) is True
    assert caller_can_view_sensitive_evidence(member_ctx) is False

    req = ResearchRequest(question="Why did checkout tickets spike?")
    assert compute_research_fingerprint(req) == compute_research_fingerprint(
        ResearchRequest(question="Why did checkout tickets spike?")
    )

    run1, _ = await service.start_research(req, admin_ctx, idempotency_key="key-1")
    run2, _ = await service.start_research(
        ResearchRequest(question="Why did checkout tickets spike?"),
        admin_ctx,
        idempotency_key="key-1",
    )
    assert run1.research_id == run2.research_id

    with pytest.raises(ResearchIdempotencyConflictError):
        await service.start_research(
            ResearchRequest(question="Completely different question"),
            admin_ctx,
            idempotency_key="key-1",
        )

    # Admin sees both read + sensitive evidence; Member has sensitive evidence filtered out
    admin_ev, admin_redacted = await service.get_evidence(run1.research_id, admin_ctx)
    assert len(admin_ev) == 2
    assert admin_redacted == 0

    member_ev, member_redacted = await service.get_evidence(run1.research_id, member_ctx)
    assert len(member_ev) == 1
    assert member_ev[0].evidence_id == "ev_01"
    assert member_redacted == 1

    # Foreign tenant gets 404 concealment
    with pytest.raises(ResearchNotFoundError):
        await service.get_run(run1.research_id, foreign_ctx)

    # Viewer without agent.invoke cannot start research
    with pytest.raises(ResearchAccessDeniedError):
        await service.start_research(ResearchRequest(question="Viewer probe"), member_ctx)

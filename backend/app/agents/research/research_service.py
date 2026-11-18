"""KEEP Phase 4.5 — KeepResearchService (Lifecycle, Re-Authorization & Runtime Coordination).

Coordinates research investigations end-to-end:
- Submits research runs through KEEP's Phase 4.2 `AgentRuntime` (invoking the
  registered `research_agent`) so every run gets full runtime telemetry,
  security enforcement, and execution lineage.
- Enforces scoped idempotency `(tenant_id, requested_by, idempotency_key)` with
  SHA-256 request fingerprinting.
- Supports both synchronous (`200`) and asynchronous (`202` via `DurableExecutionWorker`)
  execution modes plus cooperative cancellation.
- Re-verifies caller permissions on every `/report` and `/evidence` read so
  restricted (`sensitive`) passages are never leaked to callers lacking `agent.admin`
  or sensitive-access privileges.

Owner: Member 1 (Research Agent Core)
Specification: devdocs/p4/p4.5.txt (Sections 3, 4.1, 7, 8, 9)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.contracts import AgentContext, AgentRequest
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentErrorCode,
    AgentLayerError,
    ResearchAccessDeniedError,
    ResearchCancelledError,
    ResearchIdempotencyConflictError,
    ResearchNotFoundError,
    ResearchReportNotReadyError,
    sanitize_error_message,
)
from backend.app.agents.research.agent import KeepResearchAgent
from backend.app.agents.research.contracts import (
    REPORT_READY_STATUSES,
    TERMINAL_RESEARCH_STATUSES,
    EvidenceItem,
    ResearchEventRecord,
    ResearchFinding,
    ResearchReport,
    ResearchRepositoryInterface,
    ResearchRequest,
    ResearchRunRecord,
    ResearchStatus,
    compute_research_fingerprint,
)
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.workers.execution_worker import DurableExecutionWorker
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)

logger = logging.getLogger(__name__)

SENSITIVE_READ_ROLES: frozenset[str] = frozenset(
    {"orgadmin", "superadmin", "org_admin", "super_admin", "admin"}
)
SENSITIVE_READ_PERMISSIONS: frozenset[str] = frozenset(
    {"agent.manage", "agent.admin", "documents.read_sensitive", "admin.all"}
)


def caller_can_view_sensitive_evidence(context: AgentContext) -> bool:
    """Returns True if the trusted caller is authorized to inspect `sensitive` evidence passages."""
    if any(perm in SENSITIVE_READ_PERMISSIONS for perm in context.permissions):
        return True
    normalized_roles = {role.strip().lower() for role in context.roles}
    return bool(normalized_roles & SENSITIVE_READ_ROLES)


class KeepResearchService:
    """High-level KEEP service governing research investigations, reports, and provenance."""

    def __init__(
        self,
        *,
        repository: ResearchRepositoryInterface,
        research_agent: KeepResearchAgent,
        agent_runtime: AgentRuntime | None = None,
        policy: AgentPolicyInterface | None = None,
        worker: DurableExecutionWorker | None = None,
    ) -> None:
        self._repository = repository
        self._research_agent = research_agent
        self._agent_runtime = agent_runtime
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()
        self._worker = worker
        self._cancelled_ids: set[str] = set()
        if self._worker is not None:
            self._worker.bind_handler(self._execute_from_worker)

    def _require_permission(self, context: AgentContext, permission: str) -> None:
        self._policy.verify_trusted_context(context)
        if not context.has_permission(permission):
            raise ResearchAccessDeniedError(
                f"Caller lacks required permission '{permission}' for research operations."
            )

    def _check_input_guardrails(self, request: ResearchRequest, context: AgentContext) -> None:
        """Screens research question and scope against KEEP's prompt-injection guardrail."""
        probe = AgentRequest(
            goal=request.question,
            input={"scope": request.scope or "", "filters": request.filters},
            correlation_id=context.correlation_id,
        )
        self._policy.authorize_invocation(self._research_agent.metadata, probe, context)

    async def _append_event(
        self,
        research_id: str,
        tenant_id: str,
        event_type: str,
        correlation_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        await self._repository.append_event(
            ResearchEventRecord(
                research_id=research_id,
                tenant_id=tenant_id,
                event_type=event_type,
                correlation_id=correlation_id,
                details=details or {},
            )
        )

    async def start_research(
        self,
        request: ResearchRequest,
        context: AgentContext,
        *,
        mode: str = "sync",
        idempotency_key: str | None = None,
    ) -> tuple[ResearchRunRecord, ResearchReport | None]:
        """Creates and executes (sync or async) a tenant-scoped research investigation."""
        self._require_permission(context, "agent.invoke")
        self._check_input_guardrails(request, context)

        fingerprint = compute_research_fingerprint(request)
        cleaned_key = idempotency_key.strip() if isinstance(idempotency_key, str) and idempotency_key.strip() else None

        if cleaned_key:
            existing = await self._repository.find_by_idempotency_key(
                context.tenant_id,
                context.user_id,
                cleaned_key,
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ResearchIdempotencyConflictError(cleaned_key)
                report: ResearchReport | None = None
                if existing.status in REPORT_READY_STATUSES:
                    report = await self.get_report(existing.research_id, context)
                return existing, report

        now = datetime.now(UTC)
        run = ResearchRunRecord(
            research_id=request.research_id,
            tenant_id=context.tenant_id,
            requested_by=context.user_id,
            question=request.question,
            scope=request.scope,
            required_output=request.required_output,
            max_sources=request.max_sources,
            status=ResearchStatus.PENDING,
            correlation_id=context.correlation_id,
            plan_id=request.plan_id,
            workflow_execution_id=request.workflow_execution_id,
            agent_execution_id=request.agent_execution_id,
            idempotency_key=cleaned_key,
            request_fingerprint=fingerprint,
            created_at=now,
            updated_at=now,
        )
        await self._repository.create_run(run)
        await self._append_event(
            run.research_id,
            run.tenant_id,
            "research.created",
            context.correlation_id,
            {"mode": mode, "max_sources": request.max_sources, "required_output": request.required_output},
        )

        if mode == "async" and self._worker is not None:
            agent_req = AgentRequest(
                goal=request.question,
                input=request.model_dump(mode="json"),
                correlation_id=context.correlation_id,
            )
            await self._worker.enqueue(run.research_id, agent_req, context)
            await self._append_event(
                run.research_id,
                run.tenant_id,
                "research.queued",
                context.correlation_id,
                {"worker": "durable_execution_worker"},
            )
            return run, None

        completed_run, report = await self._execute_run(run, request, context)
        return completed_run, report

    async def _execute_from_worker(
        self,
        research_id: str,
        agent_request: AgentRequest,
        context: AgentContext,
    ) -> None:
        """DurableExecutionWorker handler running queued async research jobs."""
        run = await self._repository.get_run(research_id, context.tenant_id)
        if run is None or run.status in TERMINAL_RESEARCH_STATUSES:
            return
        req = ResearchRequest.model_validate(agent_request.input)
        await self._execute_run(run, req, context)

    async def _execute_run(
        self,
        run: ResearchRunRecord,
        request: ResearchRequest,
        context: AgentContext,
    ) -> tuple[ResearchRunRecord, ResearchReport | None]:
        """Executes a research run via Phase 4.2 AgentRuntime (or directly if runtime absent)."""
        if run.research_id in self._cancelled_ids:
            run.status = ResearchStatus.CANCELLED
            run.completed_at = datetime.now(UTC)
            run.updated_at = run.completed_at
            await self._repository.update_run(run)
            await self._append_event(
                run.research_id,
                run.tenant_id,
                "research.cancelled",
                context.correlation_id,
                {"stage": "pre_execution"},
            )
            return run, None

        run.status = ResearchStatus.RUNNING
        run.updated_at = datetime.now(UTC)
        await self._repository.update_run(run)
        await self._append_event(
            run.research_id,
            run.tenant_id,
            "research.started",
            context.correlation_id,
            {"agent_id": self._research_agent.metadata.agent_id},
        )

        logger.info(
            "research.started",
            extra={
                "research_id": run.research_id,
                "tenant_id": run.tenant_id,
                "correlation_id": context.correlation_id,
                "max_sources": request.max_sources,
            },
        )

        try:
            report: ResearchReport
            if self._agent_runtime is not None:
                agent_req = AgentRequest(
                    goal=request.question,
                    input=request.model_dump(mode="json"),
                    requested_capabilities=["knowledge.research"],
                    correlation_id=context.correlation_id,
                )
                execution_record = await self._agent_runtime.submit(
                    agent_id=self._research_agent.metadata.agent_id,
                    request=agent_req,
                    context=context,
                    mode="sync",
                )
                run.agent_execution_id = execution_record.execution_id
                result_payload = execution_record.result_payload or {}
                if (
                    execution_record.status.value != "SUCCEEDED"
                    or result_payload.get("status") != "succeeded"
                ):
                    err_code = (
                        execution_record.error_code
                        or result_payload.get("error_code")
                        or AgentErrorCode.AGENT_EXECUTION_FAILED.value
                    )
                    err_msg = (
                        execution_record.error_message
                        or result_payload.get("error_message")
                        or "Research execution failed in AgentRuntime."
                    )
                    run.status = ResearchStatus.FAILED
                    run.error_code = str(err_code)
                    run.error_message = sanitize_error_message(str(err_msg))
                    run.completed_at = datetime.now(UTC)
                    run.updated_at = run.completed_at
                    await self._repository.update_run(run)
                    await self._append_event(
                        run.research_id,
                        run.tenant_id,
                        "research.failed",
                        context.correlation_id,
                        {"error_code": run.error_code},
                    )
                    return run, None
                raw_report = (result_payload.get("output") or {}).get("report")
                report = ResearchReport.model_validate(raw_report)
            else:
                report = await self._research_agent.run_research(request, context)

            # Check if cooperative cancellation arrived while executing
            if run.research_id in self._cancelled_ids:
                run.status = ResearchStatus.CANCELLED
                run.completed_at = datetime.now(UTC)
                run.updated_at = run.completed_at
                await self._repository.update_run(run)
                await self._append_event(
                    run.research_id,
                    run.tenant_id,
                    "research.cancelled",
                    context.correlation_id,
                    {"stage": "post_execution"},
                )
                return run, None

            await self._repository.save_evidence(run.research_id, run.tenant_id, report.evidence)
            await self._repository.save_findings(run.research_id, run.tenant_id, report.findings)

            run.status = report.status
            run.summary = report.summary
            run.contradictions = report.contradictions
            run.unresolved_questions = report.unresolved_questions
            run.follow_up_suggestions = report.follow_up_suggestions
            run.warnings = report.warnings
            run.correction_attempts = report.correction_attempts
            run.sources_retrieved = report.sources_retrieved
            run.sources_retained = report.sources_retained
            run.retrieval_latency_ms = report.retrieval_latency_ms
            run.synthesis_latency_ms = report.synthesis_latency_ms
            run.completed_at = report.completed_at or datetime.now(UTC)
            run.updated_at = datetime.now(UTC)
            await self._repository.update_run(run)

            await self._append_event(
                run.research_id,
                run.tenant_id,
                f"research.{report.status.value}",
                context.correlation_id,
                {
                    "sources_retrieved": report.sources_retrieved,
                    "sources_retained": report.sources_retained,
                    "findings_count": len(report.findings),
                    "contradictions_count": len(report.contradictions),
                    "correction_attempts": report.correction_attempts,
                    "retrieval_latency_ms": report.retrieval_latency_ms,
                    "synthesis_latency_ms": report.synthesis_latency_ms,
                },
            )
            logger.info(
                "research.completed",
                extra={
                    "research_id": run.research_id,
                    "tenant_id": run.tenant_id,
                    "correlation_id": context.correlation_id,
                    "status": report.status.value,
                    "sources_retrieved": report.sources_retrieved,
                    "sources_retained": report.sources_retained,
                    "correction_attempts": report.correction_attempts,
                },
            )
            return run, report

        except AgentLayerError as exc:
            run.status = ResearchStatus.FAILED
            run.error_code = exc.code.value
            run.error_message = sanitize_error_message(str(exc))
            run.completed_at = datetime.now(UTC)
            run.updated_at = run.completed_at
            await self._repository.update_run(run)
            await self._append_event(
                run.research_id,
                run.tenant_id,
                "research.failed",
                context.correlation_id,
                {"error_code": run.error_code},
            )
            raise
        except Exception as exc:  # noqa: BLE001 - ensure run transitions to terminal FAILED state
            run.status = ResearchStatus.FAILED
            run.error_code = AgentErrorCode.AGENT_EXECUTION_FAILED.value
            run.error_message = sanitize_error_message(f"Unexpected research failure: {exc}")
            run.completed_at = datetime.now(UTC)
            run.updated_at = run.completed_at
            await self._repository.update_run(run)
            await self._append_event(
                run.research_id,
                run.tenant_id,
                "research.failed",
                context.correlation_id,
                {"error_code": run.error_code},
            )
            return run, None

    async def get_run(self, research_id: str, context: AgentContext) -> ResearchRunRecord:
        """Retrieves tenant-scoped research metadata (conceals foreign tenant runs with 404)."""
        self._require_permission(context, "agent.view")
        run = await self._repository.get_run(research_id, context.tenant_id)
        if run is None:
            raise ResearchNotFoundError(research_id)
        return run

    async def list_runs(
        self,
        context: AgentContext,
        *,
        status: ResearchStatus | None = None,
        limit: int = 50,
    ) -> list[ResearchRunRecord]:
        """Lists research investigations scoped strictly to `context.tenant_id`."""
        self._require_permission(context, "agent.view")
        capped = max(1, min(200, limit))
        return await self._repository.list_runs(context.tenant_id, status=status, limit=capped)

    def _filter_authorized_evidence(
        self,
        evidence: list[EvidenceItem],
        context: AgentContext,
    ) -> tuple[list[EvidenceItem], int]:
        """Re-verifies caller clearance on persisted evidence passages."""
        allow_sensitive = caller_can_view_sensitive_evidence(context)
        authorized: list[EvidenceItem] = []
        redacted_count = 0
        for item in evidence:
            if item.access_tier == "sensitive" and not allow_sensitive:
                redacted_count += 1
                continue
            authorized.append(item)
        return authorized, redacted_count

    async def get_evidence(
        self,
        research_id: str,
        context: AgentContext,
    ) -> tuple[list[EvidenceItem], int]:
        """Returns re-authorized evidence passages and count of restricted passages omitted."""
        run = await self.get_run(research_id, context)
        raw_evidence = await self._repository.get_evidence(run.research_id, context.tenant_id)
        return self._filter_authorized_evidence(raw_evidence, context)

    async def get_report(self, research_id: str, context: AgentContext) -> ResearchReport:
        """Returns a re-authorized ResearchReport with restricted citations filtered for current caller."""
        run = await self.get_run(research_id, context)
        if run.status not in REPORT_READY_STATUSES:
            raise ResearchReportNotReadyError(run.research_id, run.status.value)

        raw_evidence = await self._repository.get_evidence(run.research_id, context.tenant_id)
        authorized_evidence, redacted_count = self._filter_authorized_evidence(raw_evidence, context)
        allowed_evidence_ids = {item.evidence_id for item in authorized_evidence}

        raw_findings = await self._repository.get_findings(run.research_id, context.tenant_id)
        filtered_findings: list[ResearchFinding] = []
        for finding in raw_findings:
            visible_ids = [eid for eid in finding.evidence_ids if eid in allowed_evidence_ids]
            if finding.claim_type == "factual" and finding.evidence_ids and not visible_ids:
                # Omit findings backed solely by restricted evidence the current caller cannot view
                continue
            filtered_findings.append(finding.model_copy(update={"evidence_ids": visible_ids}))

        warnings = list(run.warnings)
        if redacted_count > 0:
            warnings.append(
                f"{redacted_count} restricted evidence passage(s) were omitted based on your current access permissions."
            )

        return ResearchReport(
            research_id=run.research_id,
            question=run.question,
            scope=run.scope,
            required_output=run.required_output,
            status=run.status,
            summary=run.summary or "",
            findings=filtered_findings,
            evidence=authorized_evidence,
            contradictions=[
                c
                for c in run.contradictions
                if not c.evidence_ids or any(eid in allowed_evidence_ids for eid in c.evidence_ids)
            ],
            unresolved_questions=list(run.unresolved_questions),
            follow_up_suggestions=list(run.follow_up_suggestions),
            warnings=list(dict.fromkeys(warnings)),
            correction_attempts=run.correction_attempts,
            sources_retrieved=run.sources_retrieved,
            sources_retained=len(authorized_evidence),
            retrieval_latency_ms=run.retrieval_latency_ms,
            synthesis_latency_ms=run.synthesis_latency_ms,
            correlation_id=run.correlation_id,
            completed_at=run.completed_at,
        )

    async def get_events(self, research_id: str, context: AgentContext) -> list[ResearchEventRecord]:
        """Returns tenant-scoped audit trail events for a research investigation."""
        run = await self.get_run(research_id, context)
        return await self._repository.list_events(run.research_id, context.tenant_id)

    async def cancel_research(
        self,
        research_id: str,
        context: AgentContext,
    ) -> ResearchRunRecord:
        """Cooperatively cancels a pending or running research investigation."""
        self._require_permission(context, "agent.invoke")
        run = await self._repository.get_run(research_id, context.tenant_id)
        if run is None:
            raise ResearchNotFoundError(research_id)
        if run.status in TERMINAL_RESEARCH_STATUSES:
            raise ResearchCancelledError(research_id)

        self._cancelled_ids.add(research_id)
        if run.status == ResearchStatus.PENDING:
            run.status = ResearchStatus.CANCELLED
            run.completed_at = datetime.now(UTC)
            run.updated_at = run.completed_at
            await self._repository.update_run(run)
        await self._append_event(
            run.research_id,
            run.tenant_id,
            "research.cancel_requested",
            context.correlation_id,
            {"requested_by": context.user_id},
        )
        return run


__all__ = [
    "AgentAuthorizationError",
    "KeepResearchService",
    "caller_can_view_sensitive_evidence",
]

"""Phase 4.11 — Central Proactive Enterprise Intelligence Service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from backend.app.agents.errors import (
    IntelligenceAccessDeniedError,
    IntelligenceInsightNotFoundError,
    IntelligenceRunNotFoundError,
    IntelligenceScanRejectedError,
)
from backend.app.agents.intelligence.contracts import (
    DetectionRunRecord,
    EvidenceReference,
    InsightCategory,
    InsightDismissRequest,
    InsightFeedbackRecord,
    InsightFeedbackRequest,
    InsightInvestigateRequest,
    InsightResolveRequest,
    InsightStatus,
    IntelligenceAuditEvent,
    IntelligenceCandidate,
    IntelligenceInsight,
    IntelligenceSecurityContext,
    OperationalMetrics,
    ScanRequest,
)
from backend.app.agents.intelligence.deduplication import (
    build_suppression_record,
    compute_dedup_key,
    is_suppressed,
)
from backend.app.agents.intelligence.insight_registry import InsightRegistry
from backend.app.agents.intelligence.models import validate_insight_transition
from backend.app.agents.intelligence.prioritization import (
    RANKING_VERSION,
    rank_insights,
    score_candidate,
)
from backend.app.agents.intelligence.repository import (
    BaseIntelligenceRepository,
    InMemoryIntelligenceRepository,
)


class DetectorProtocol(Protocol):
    @property
    def detector_id(self) -> str: ...

    @property
    def version(self) -> str: ...

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]: ...


class EvidenceValidatorProtocol(Protocol):
    async def validate(
        self,
        candidate: IntelligenceCandidate,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, list[EvidenceReference], list[str]]: ...


class PolicyEngineProtocol(Protocol):
    def authorize_read(self, ctx: IntelligenceSecurityContext) -> None: ...
    def authorize_scan(self, ctx: IntelligenceSecurityContext) -> None: ...
    def authorize_org_action(self, ctx: IntelligenceSecurityContext) -> None: ...
    def filter_visible_insights(
        self,
        insights: list[IntelligenceInsight],
        ctx: IntelligenceSecurityContext,
        user_dismissed_keys: set[str],
    ) -> list[IntelligenceInsight]: ...
    def check_publication_policy(
        self,
        candidate: IntelligenceCandidate,
        priority_score: float,
        evidence_valid: bool,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, str | None]: ...
    def sanitize_summary(self, text: str) -> str: ...


class _DefaultEvidenceValidator:
    async def validate(
        self,
        candidate: IntelligenceCandidate,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, list[EvidenceReference], list[str]]:
        limitations = list(candidate.limitations)
        if candidate.evidence_details:
            records = list(candidate.evidence_details)
        else:
            records = [
                EvidenceReference(resource_ref=ref, source_type="document", validation_outcome="valid")
                for ref in candidate.evidence_refs
            ]

        if not records and not candidate.allow_evidence_free:
            limitations.append("Missing verified evidence references.")
            return False, records, limitations
        return True, records, limitations


class _DefaultPolicyEngine:
    def authorize_read(self, ctx: IntelligenceSecurityContext) -> None:
        if not ctx.tenant_id or not ctx.user_id:
            raise IntelligenceAccessDeniedError("Authenticated tenant and user context required.")

    def authorize_scan(self, ctx: IntelligenceSecurityContext) -> None:
        self.authorize_read(ctx)
        if (
            ctx.permissions
            and "agent.invoke" not in ctx.permissions
            and "agent.manage" not in ctx.permissions
            and "admin" not in [r.lower() for r in ctx.roles]
        ):
            raise IntelligenceAccessDeniedError("Caller lacks scan invocation permission.")

    def authorize_org_action(self, ctx: IntelligenceSecurityContext) -> None:
        self.authorize_read(ctx)
        if "agent.manage" not in ctx.permissions and not any(
            r.lower() in ("admin", "lead", "owner", "super_admin") for r in ctx.roles
        ):
            raise IntelligenceAccessDeniedError("Organization-wide insight action requires elevated role.")

    def filter_visible_insights(
        self,
        insights: list[IntelligenceInsight],
        ctx: IntelligenceSecurityContext,
        user_dismissed_keys: set[str],
    ) -> list[IntelligenceInsight]:
        caller_roles = {r.lower() for r in ctx.roles}
        visible: list[IntelligenceInsight] = []
        for ins in insights:
            if ins.dedup_key in user_dismissed_keys:
                continue
            if ins.audience_roles:
                allowed = {r.lower() for r in ins.audience_roles}
                if not caller_roles.intersection(allowed) and not caller_roles.intersection({"admin", "super_admin"}):
                    continue
            if ctx.accessible_resource_refs is not None and ins.evidence_refs:
                allowed_refs = set(ctx.accessible_resource_refs)
                if not set(ins.evidence_refs).issubset(allowed_refs):
                    continue
            visible.append(ins)
        return visible

    def check_publication_policy(
        self,
        candidate: IntelligenceCandidate,
        priority_score: float,
        evidence_valid: bool,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, str | None]:
        if not evidence_valid and not candidate.allow_evidence_free:
            return False, "Withheld: insufficient verified evidence."
        if priority_score < 20.0:
            return False, f"Withheld: priority score {priority_score:.1f} below publication threshold."
        return True, None

    def sanitize_summary(self, text: str) -> str:
        return text


class IntelligenceService:
    """Central proactive intelligence engine coordinating detection, validation, ranking, and lifecycle."""

    def __init__(
        self,
        repository: BaseIntelligenceRepository | None = None,
        detectors: list[DetectorProtocol] | None = None,
        evidence_validator: EvidenceValidatorProtocol | None = None,
        policy_engine: PolicyEngineProtocol | None = None,
        registry: InsightRegistry | None = None,
        orchestration_dispatcher: Any | None = None,
    ) -> None:
        self.repository = repository or InMemoryIntelligenceRepository()
        self.detectors: dict[str, DetectorProtocol] = {}
        self.evidence_validator: EvidenceValidatorProtocol = evidence_validator or _DefaultEvidenceValidator()
        self.policy_engine: PolicyEngineProtocol = policy_engine or _DefaultPolicyEngine()
        self.registry = registry or InsightRegistry()
        self.orchestration_dispatcher = orchestration_dispatcher
        for d in detectors or []:
            self.register_detector(d)

    def register_detector(self, detector: DetectorProtocol) -> None:
        self.detectors[detector.detector_id] = detector
        self.registry.register_detector_version(detector.detector_id, detector.version)

    async def run_scan(
        self,
        request: ScanRequest,
        ctx: IntelligenceSecurityContext,
    ) -> DetectionRunRecord:
        self.policy_engine.authorize_scan(ctx)
        if not request.observations:
            raise IntelligenceScanRejectedError("Scan request must include at least one observation.")

        selected_detectors: list[DetectorProtocol] = []
        if request.detector_ids:
            for det_id in request.detector_ids:
                if det_id in self.detectors:
                    selected_detectors.append(self.detectors[det_id])
        else:
            selected_detectors = list(self.detectors.values())

        run = DetectionRunRecord(
            tenant_id=ctx.tenant_id,
            trigger_source=request.trigger_source,
            source_event_id=request.source_event_id,
            detector_versions={d.detector_id: d.version for d in selected_detectors},
            status="running",
        )
        await self.repository.create_run(run)

        sec_dict = {
            "tenant_id": ctx.tenant_id,
            "user_id": ctx.user_id,
            "roles": list(ctx.roles),
            "permissions": list(ctx.permissions),
            "accessible_resource_refs": ctx.accessible_resource_refs,
        }
        active_suppressions = await self.repository.list_active_suppressions(ctx.tenant_id)

        raw_candidates: list[IntelligenceCandidate] = []
        for obs in request.observations:
            if obs.get("tenant_id") and obs.get("tenant_id") != ctx.tenant_id:
                continue
            for detector in selected_detectors:
                try:
                    found = await detector.detect(obs, sec_dict)
                    for item in found:
                        cand = (
                            item
                            if isinstance(item, IntelligenceCandidate)
                            else IntelligenceCandidate.model_validate(item)
                        )
                        if cand.detector_id == "unknown":
                            cand.detector_id = detector.detector_id
                            cand.detector_version = detector.version
                        raw_candidates.append(cand)
                except Exception as exc:  # noqa: BLE001 — isolate detector crashes so run telemetry persists
                    run.detector_errors.append(
                        {"detector_id": detector.detector_id, "error": str(exc)[:300]}
                    )
                    await self.repository.add_audit_event(
                        IntelligenceAuditEvent(
                            tenant_id=ctx.tenant_id,
                            run_id=run.run_id,
                            action="run.detector_failed",
                            actor_id=ctx.user_id,
                            reason=str(exc)[:300],
                            details={"detector_id": detector.detector_id},
                        )
                    )

        run.candidates_generated = len(raw_candidates)
        seen_in_run: set[str] = set()

        for cand in raw_candidates:
            evidence_ok, evidence_records, limitations = await self.evidence_validator.validate(cand, ctx)
            cand.limitations = limitations
            if not evidence_ok and cand.evidence_quality_score > 0.35:
                cand.evidence_quality_score = 0.25

            priority = score_candidate(cand)
            dedup_key = compute_dedup_key(ctx.tenant_id, cand)
            suppressed, sup_reason = is_suppressed(active_suppressions, dedup_key)
            if not suppressed and dedup_key in seen_in_run:
                suppressed, sup_reason = True, "Duplicate candidate within the same detection run."

            permitted, policy_reason = self.policy_engine.check_publication_policy(
                cand, priority, evidence_ok, ctx
            )

            status: InsightStatus
            if suppressed:
                status = "suppressed"
                run.insights_suppressed += 1
                action = "insight.suppressed"
                reason = sup_reason
            elif not permitted:
                status = "withheld"
                action = "insight.withheld"
                reason = policy_reason
            else:
                status = "published"
                run.insights_published += 1
                seen_in_run.add(dedup_key)
                action = "insight.published"
                reason = "Evidence and policy checks passed."
                if request.suppress_window_seconds > 0:
                    sup = build_suppression_record(
                        tenant_id=ctx.tenant_id,
                        dedup_key=dedup_key,
                        reason="Active deduplication cooldown window.",
                        window_seconds=request.suppress_window_seconds,
                        scope="tenant",
                    )
                    await self.repository.add_suppression(sup)
                    active_suppressions.append(sup)

            insight = IntelligenceInsight(
                tenant_id=ctx.tenant_id,
                run_id=run.run_id,
                category=cand.category,
                title=cand.title,
                summary=self.policy_engine.sanitize_summary(cand.summary),
                observed_facts=cand.observed_facts,
                inferred_explanation=cand.inferred_explanation,
                limitations=cand.limitations,
                evidence_refs=[e.resource_ref for e in evidence_records] or cand.evidence_refs,
                evidence_records=evidence_records,
                affected_resource_refs=cand.affected_resource_refs,
                audience_roles=cand.audience_roles,
                impact_score=cand.impact_score,
                relevance_score=cand.relevance_score,
                evidence_quality_score=cand.evidence_quality_score,
                urgency_score=cand.urgency_score,
                novelty_score=cand.novelty_score,
                priority_score=priority,
                confidence_score=cand.confidence_score,
                status=status,
                dedup_key=dedup_key,
                detector_id=cand.detector_id,
                detector_version=cand.detector_version,
                ranking_version=RANKING_VERSION,
                source_freshness_at=cand.source_freshness_at,
            )
            await self.repository.save_insight(insight)
            await self.repository.save_evidence(ctx.tenant_id, insight.insight_id, evidence_records)
            await self.repository.add_audit_event(
                IntelligenceAuditEvent(
                    tenant_id=ctx.tenant_id,
                    insight_id=insight.insight_id,
                    run_id=run.run_id,
                    action=action,
                    actor_id=ctx.user_id,
                    reason=reason,
                    details={"category": cand.category, "priority_score": priority},
                )
            )

        run.status = "completed_with_errors" if run.detector_errors else "completed"
        run.completed_at = datetime.now(UTC)
        await self.repository.update_run(run)
        return run

    async def list_insights(
        self,
        ctx: IntelligenceSecurityContext,
        *,
        category: InsightCategory | None = None,
        status: InsightStatus | None = "published",
        min_priority: float | None = None,
        limit: int = 100,
    ) -> list[IntelligenceInsight]:
        self.policy_engine.authorize_read(ctx)
        items = await self.repository.list_insights(
            ctx.tenant_id,
            category=category,
            status=status,
            min_priority=min_priority,
            limit=limit,
        )
        active_suppressions = await self.repository.list_active_suppressions(ctx.tenant_id)
        user_dismissed_keys = {
            s.dedup_key
            for s in active_suppressions
            if s.scope == "user" and s.user_id == ctx.user_id
        }
        visible = self.policy_engine.filter_visible_insights(items, ctx, user_dismissed_keys)
        return rank_insights(visible)

    async def get_insight(
        self,
        insight_id: str,
        ctx: IntelligenceSecurityContext,
    ) -> IntelligenceInsight:
        self.policy_engine.authorize_read(ctx)
        ins = await self.repository.get_insight(ctx.tenant_id, insight_id)
        if ins is None:
            raise IntelligenceInsightNotFoundError(insight_id)
        visible = self.policy_engine.filter_visible_insights([ins], ctx, set())
        if not visible:
            raise IntelligenceAccessDeniedError("Caller is not authorized to view this insight or its sources.")
        evidence = await self.repository.get_evidence(ctx.tenant_id, insight_id)
        ins.evidence_records = evidence
        return ins

    async def get_insight_evidence(
        self,
        insight_id: str,
        ctx: IntelligenceSecurityContext,
    ) -> list[EvidenceReference]:
        ins = await self.get_insight(insight_id, ctx)
        return ins.evidence_records

    async def submit_feedback(
        self,
        insight_id: str,
        req: InsightFeedbackRequest,
        ctx: IntelligenceSecurityContext,
    ) -> InsightFeedbackRecord:
        await self.get_insight(insight_id, ctx)
        record = InsightFeedbackRecord(
            insight_id=insight_id,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            feedback=req.feedback,
            comment=req.comment,
            scope="user",
        )
        await self.repository.add_feedback(record)
        await self.repository.add_audit_event(
            IntelligenceAuditEvent(
                tenant_id=ctx.tenant_id,
                insight_id=insight_id,
                action="insight.feedback",
                actor_id=ctx.user_id,
                reason=req.feedback,
                details={"comment": req.comment} if req.comment else {},
            )
        )
        return record

    async def dismiss_insight(
        self,
        insight_id: str,
        req: InsightDismissRequest,
        ctx: IntelligenceSecurityContext,
    ) -> IntelligenceInsight:
        ins = await self.get_insight(insight_id, ctx)
        if req.scope == "organization":
            self.policy_engine.authorize_org_action(ctx)
            validate_insight_transition(insight_id, ins.status, "dismissed")
            ins.status = "dismissed"
            ins.updated_at = datetime.now(UTC)
            await self.repository.update_insight(ins)
        else:
            sup = build_suppression_record(
                tenant_id=ctx.tenant_id,
                dedup_key=ins.dedup_key,
                reason=req.reason or "Dismissed in user feed.",
                window_seconds=86400 * 30,
                scope="user",
                user_id=ctx.user_id,
            )
            await self.repository.add_suppression(sup)

        await self.repository.add_audit_event(
            IntelligenceAuditEvent(
                tenant_id=ctx.tenant_id,
                insight_id=insight_id,
                action="insight.dismissed",
                actor_id=ctx.user_id,
                reason=req.reason,
                details={"scope": req.scope},
            )
        )
        return ins

    async def resolve_insight(
        self,
        insight_id: str,
        req: InsightResolveRequest,
        ctx: IntelligenceSecurityContext,
    ) -> IntelligenceInsight:
        ins = await self.get_insight(insight_id, ctx)
        validate_insight_transition(insight_id, ins.status, "resolved")
        ins.status = "resolved"
        ins.updated_at = datetime.now(UTC)
        await self.repository.update_insight(ins)
        await self.repository.add_audit_event(
            IntelligenceAuditEvent(
                tenant_id=ctx.tenant_id,
                insight_id=insight_id,
                action="insight.resolved",
                actor_id=ctx.user_id,
                reason=req.resolution_note,
            )
        )
        return ins

    async def investigate_insight(
        self,
        insight_id: str,
        req: InsightInvestigateRequest,
        ctx: IntelligenceSecurityContext,
    ) -> IntelligenceInsight:
        self.policy_engine.authorize_scan(ctx)
        ins = await self.get_insight(insight_id, ctx)
        validate_insight_transition(insight_id, ins.status, "investigating")

        workflow_exec_id: str | None = None
        if self.orchestration_dispatcher is not None:
            workflow_exec_id = await self.orchestration_dispatcher(ins, req.workflow_id, ctx, req.notes)

        ins.status = "investigating"
        ins.workflow_execution_id = workflow_exec_id
        ins.updated_at = datetime.now(UTC)
        await self.repository.update_insight(ins)
        await self.repository.add_audit_event(
            IntelligenceAuditEvent(
                tenant_id=ctx.tenant_id,
                insight_id=insight_id,
                action="insight.investigating",
                actor_id=ctx.user_id,
                reason=f"Launched workflow '{req.workflow_id}'",
                details={"workflow_execution_id": workflow_exec_id},
            )
        )
        return ins

    async def get_run(
        self,
        run_id: str,
        ctx: IntelligenceSecurityContext,
    ) -> DetectionRunRecord:
        self.policy_engine.authorize_read(ctx)
        run = await self.repository.get_run(ctx.tenant_id, run_id)
        if run is None:
            raise IntelligenceRunNotFoundError(run_id)
        return run

    async def get_metrics(self, ctx: IntelligenceSecurityContext) -> OperationalMetrics:
        self.policy_engine.authorize_read(ctx)
        runs = await self.repository.list_runs(ctx.tenant_id, limit=500)
        all_insights = await self.repository.list_insights(ctx.tenant_id, status=None, limit=1000)
        feedbacks = await self.repository.list_feedback(ctx.tenant_id)

        published = sum(1 for i in all_insights if i.status == "published")
        suppressed = sum(1 for i in all_insights if i.status == "suppressed")
        withheld = sum(1 for i in all_insights if i.status == "withheld")
        dismissed = sum(1 for i in all_insights if i.status == "dismissed")
        resolved = sum(1 for i in all_insights if i.status == "resolved")
        total_candidates = sum(r.candidates_generated for r in runs)
        dup_rate = round(suppressed / total_candidates, 4) if total_candidates > 0 else 0.0

        fb_counts: dict[str, int] = {}
        for fb in feedbacks:
            fb_counts[fb.feedback] = fb_counts.get(fb.feedback, 0) + 1

        cat_counts: dict[str, int] = {}
        for ins in all_insights:
            cat_counts[ins.category] = cat_counts.get(ins.category, 0) + 1

        return OperationalMetrics(
            tenant_id=ctx.tenant_id,
            total_runs=len(runs),
            total_candidates=total_candidates,
            published_insights=published,
            suppressed_insights=suppressed,
            withheld_insights=withheld,
            dismissed_insights=dismissed,
            resolved_insights=resolved,
            duplicate_suppression_rate=dup_rate,
            feedback_counts=fb_counts,
            category_counts=cat_counts,
        )

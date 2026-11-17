"""KEEP Phase 4.3 — Multi-Agent Orchestration Service.

Coordinates workflow submission, version pinning, scoped idempotency deduplication,
durable workflow persistence, graph execution through the LangGraph adapter seam,
cooperative cancellation, and safe checkpoint recovery with mandatory re-authorization.

Owner: Member 1 (Orchestration Architecture & Workflow Registry)
Specification: devdocs/p4/p4.3.txt (Sections 2, 3, 8, 9, 10, 11)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.agents.contracts import AgentContext, EvidenceReference
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentErrorCode,
    AgentLayerError,
    WorkflowCancelledError,
    WorkflowExecutionNotFoundError,
    WorkflowIdempotencyConflictError,
    WorkflowRecoveryNotAllowedError,
    WorkflowResultNotReadyError,
    WorkflowTimeoutError,
    sanitize_error_message,
)
from backend.app.agents.orchestration.workflow_contracts import (
    TERMINAL_WORKFLOW_STATUSES,
    WorkflowBackgroundDispatcher,
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowObserverInterface,
    WorkflowRepositoryInterface,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepLink,
    compute_workflow_fingerprint,
)
from backend.app.agents.orchestration.workflow_registry import WorkflowRegistry
from backend.app.services.security.agent_permissions import AgentPermissionEvaluator
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)


class _NoOpWorkflowObserver:
    def record_event(
        self,
        event_type: str,
        *,
        record: WorkflowExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None:
        return None

    def record_step(self, step: WorkflowStepLink, *, correlation_id: str) -> None:
        return None


class KeepOrchestrationService:
    """Top-level KEEP orchestration engine facade coordinating workflows over Phase 4.2 AgentRuntime."""

    def __init__(
        self,
        *,
        workflow_registry: WorkflowRegistry,
        repository: WorkflowRepositoryInterface,
        runtime: Any,
        policy: Any | None = None,
        security_policy: AgentPolicyInterface | None = None,
        checkpoint_store: Any | None = None,
        dispatcher: WorkflowBackgroundDispatcher | None = None,
        observer: WorkflowObserverInterface | None = None,
        permission_evaluator: AgentPermissionEvaluator | None = None,
    ) -> None:
        self.workflow_registry = workflow_registry
        self.repository = repository
        self.runtime = runtime
        self.workflow_policy = policy
        self.permission_evaluator = permission_evaluator or AgentPermissionEvaluator()
        self.security_policy: AgentPolicyInterface = security_policy or KeepAgentPolicyEngine(
            permission_evaluator=self.permission_evaluator
        )
        self.checkpoint_store = checkpoint_store
        self.dispatcher = dispatcher
        self.observer: WorkflowObserverInterface = observer or _NoOpWorkflowObserver()
        self._active_tasks: dict[str, asyncio.Task[Any]] = {}
        self._cancel_flags: set[str] = set()

    # ------------------------------------------------------------------
    # Workflow Registry Discovery & Admin Management
    # ------------------------------------------------------------------

    def list_workflows(
        self,
        context: AgentContext,
        *,
        include_disabled: bool = False,
        task_type: str | None = None,
    ) -> list[dict[str, Any]]:
        self.security_policy.verify_trusted_context(context)
        can_see_disabled = (
            include_disabled and self.permission_evaluator.can_view_disabled_agents(context)
        )
        return self.workflow_registry.list_workflows(
            include_disabled=can_see_disabled,
            task_type=task_type,
        )

    def get_workflow_definition(
        self,
        workflow_id: str,
        context: AgentContext,
        *,
        version: str | None = None,
    ) -> WorkflowDefinition:
        self.security_policy.verify_trusted_context(context)
        defn = self.workflow_registry.get_definition(
            workflow_id,
            version=version,
            allow_disabled=True,
        )
        if not defn.enabled and not self.permission_evaluator.can_view_disabled_agents(context):
            raise AgentAuthorizationError(
                f"Caller is not authorized to inspect disabled workflow '{defn.workflow_id}'.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )
        return defn

    def set_workflow_enabled(
        self,
        workflow_id: str,
        enabled: bool,
        context: AgentContext,
        *,
        version: str | None = None,
    ) -> WorkflowDefinition:
        self.security_policy.verify_trusted_context(context)
        if not self.permission_evaluator.can_manage_agents(context):
            raise AgentAuthorizationError(
                "Only OrgAdmin or SuperAdmin may enable or disable workflows.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )
        return self.workflow_registry.set_enabled(workflow_id, enabled, version=version)

    # ------------------------------------------------------------------
    # Workflow Submission, Execution & Lifecycle
    # ------------------------------------------------------------------

    async def submit_workflow(
        self,
        workflow_id: str,
        request: WorkflowRequest,
        context: AgentContext,
        *,
        idempotency_key: str | None = None,
    ) -> WorkflowExecutionRecord:
        """Validates policy, pins workflow version, persists PENDING record, and executes or enqueues."""
        self.security_policy.verify_trusted_context(context)

        definition, _factory = self.workflow_registry.get(
            workflow_id,
            version=request.version,
            allow_disabled=False,
        )

        # Enforce workflow-level policy (input size, RBAC, prompt injection, timeout clamping)
        if self.workflow_policy is not None:
            effective_timeout = self.workflow_policy.authorize_submission(
                definition, request, context
            )
        else:
            effective_timeout = min(
                request.timeout_seconds or definition.default_timeout_seconds,
                definition.max_timeout_seconds,
            )

        effective_idem_key = idempotency_key or request.idempotency_key
        fingerprint = compute_workflow_fingerprint(
            definition.workflow_id,
            definition.version,
            request.goal,
            request.input,
        )

        # Scoped idempotency deduplication & conflict check
        if effective_idem_key:
            existing = await self.repository.get_by_idempotency_key(
                context.tenant_id,
                context.user_id,
                effective_idem_key,
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise WorkflowIdempotencyConflictError(effective_idem_key)
                self.observer.record_event(
                    "workflow.idempotent_replay",
                    record=existing,
                    details={"idempotency_key": effective_idem_key},
                )
                return existing

        correlation_id = request.correlation_id or context.correlation_id
        now = datetime.now(UTC)
        deadline_at = now + timedelta(seconds=effective_timeout)

        record = WorkflowExecutionRecord(
            workflow_id=definition.workflow_id,
            workflow_version=definition.version,
            tenant_id=context.tenant_id,
            requested_by=context.user_id,
            status=WorkflowStatus.PENDING,
            mode=request.mode,
            goal=request.goal,
            input=dict(request.input),
            correlation_id=correlation_id,
            idempotency_key=effective_idem_key,
            request_fingerprint=fingerprint,
            deadline_at=deadline_at,
        )

        # Persist BEFORE reporting accepted (devdocs/p4/p4.3.txt Section 8)
        persisted = await self.repository.create(record)
        self.observer.record_event("workflow.created", record=persisted)

        if request.mode == "sync":
            return await self.execute_existing(persisted.workflow_execution_id, context)

        if self.dispatcher is not None:
            await self.dispatcher.enqueue(persisted.workflow_execution_id, context)
            self.observer.record_event("workflow.queued", record=persisted)
            return persisted

        # Fallback to background asyncio task if no dedicated worker was bound
        task = asyncio.create_task(
            self.execute_existing(persisted.workflow_execution_id, context)
        )
        self._active_tasks[persisted.workflow_execution_id] = task
        task.add_done_callback(lambda _t: self._active_tasks.pop(persisted.workflow_execution_id, None))
        return persisted

    async def execute_existing(
        self,
        workflow_execution_id: str,
        context: AgentContext,
        *,
        resume_state: dict[str, Any] | None = None,
        completed_nodes: set[str] | None = None,
        allow_from_recoverable: bool = False,
    ) -> WorkflowExecutionRecord:
        """Executes a persisted workflow execution pinned to its recorded version."""
        record = await self.repository.get(workflow_execution_id, context.tenant_id)
        if record is None:
            raise WorkflowExecutionNotFoundError(workflow_execution_id)

        if record.status == WorkflowStatus.CANCELLED or workflow_execution_id in self._cancel_flags:
            return record

        # Retrieve PINNED workflow version (allow_disabled=True so in-flight runs finish safely)
        definition, factory = self.workflow_registry.get(
            record.workflow_id,
            version=record.workflow_version,
            allow_disabled=True,
        )

        started_at = datetime.now(UTC)
        timeout_seconds = definition.default_timeout_seconds
        if record.deadline_at is not None and not allow_from_recoverable:
            remaining = (record.deadline_at - started_at).total_seconds()
            timeout_seconds = max(0.05, remaining)
        elif allow_from_recoverable:
            record.deadline_at = started_at + timedelta(seconds=definition.default_timeout_seconds)

        # Acquire concurrency budget slot if workflow policy supports it
        slot_acquired = False
        if self.workflow_policy is not None and hasattr(self.workflow_policy, "acquire_slot"):
            self.workflow_policy.acquire_slot(context.tenant_id, workflow_execution_id)
            slot_acquired = True

        try:
            running_record = await self.repository.mark_running(
                workflow_execution_id,
                context.tenant_id,
                started_at=started_at,
                deadline_at=record.deadline_at,
                allow_from_recoverable=allow_from_recoverable,
            )
            self.observer.record_event(
                "workflow.resumed" if allow_from_recoverable else "workflow.started",
                record=running_record,
            )

            async def _on_step(step: WorkflowStepLink) -> None:
                await self.repository.append_step(
                    workflow_execution_id,
                    context.tenant_id,
                    step,
                )
                self.observer.record_step(step, correlation_id=running_record.correlation_id)

            async def _on_checkpoint(step_name: str, step_number: int, state: dict[str, Any]) -> None:
                if self.checkpoint_store is not None:
                    chk = await self.checkpoint_store.save_workflow_checkpoint(
                        workflow_execution_id=workflow_execution_id,
                        step_name=step_name,
                        step_number=step_number,
                        state=state,
                        context=context,
                    )
                    await self.repository.update_checkpoint_ref(
                        workflow_execution_id,
                        context.tenant_id,
                        chk.checkpoint_id,
                    )

            def _is_cancelled() -> bool:
                return workflow_execution_id in self._cancel_flags

            graph = factory(
                runtime=self.runtime,
                definition=definition,
                on_step=_on_step,
                workflow_policy=self.workflow_policy,
            )

            initial_state: dict[str, Any] = {
                "state_version": "1.0",
                "workflow_id": definition.workflow_id,
                "workflow_version": definition.version,
                "workflow_execution_id": workflow_execution_id,
                "tenant_id": context.tenant_id,
                "requested_by": context.user_id,
                "correlation_id": running_record.correlation_id,
                "goal": running_record.goal,
                "input": dict(running_record.input),
                "execution_ids": list(running_record.execution_ids),
                "warnings": list(running_record.warnings),
                "failed_optional_steps": [],
                "evidence": [],
                "branch_results": {},
                "completed_nodes": sorted(completed_nodes) if completed_nodes else [],
            }
            if resume_state:
                for key in (
                    "research_result",
                    "analysis_result",
                    "branch_results",
                    "evidence",
                    "execution_ids",
                    "warnings",
                    "failed_optional_steps",
                ):
                    if key in resume_state:
                        initial_state[key] = resume_state[key]

            coro = graph.arun(
                initial_state,
                context=context,
                completed_nodes=completed_nodes,
                checkpoint_callback=_on_checkpoint,
                cancel_checker=_is_cancelled,
            )
            final_state = await asyncio.wait_for(coro, timeout=timeout_seconds)

            # Check if cancellation raced with completion
            if _is_cancelled():
                raise WorkflowCancelledError(workflow_execution_id)

            completed_at = datetime.now(UTC)
            duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))

            final_status_str = str(final_state.get("workflow_status") or WorkflowStatus.SUCCEEDED.value)
            try:
                final_status = WorkflowStatus(final_status_str)
            except ValueError:
                final_status = WorkflowStatus.SUCCEEDED

            raw_evidence = final_state.get("evidence") or []
            validated_evidence = [
                ev if isinstance(ev, EvidenceReference) else EvidenceReference.model_validate(ev)
                for ev in raw_evidence
            ]
            warnings = [str(w) for w in (final_state.get("warnings") or [])]
            failed_optional = [str(s) for s in (final_state.get("failed_optional_steps") or [])]
            exec_ids = [str(eid) for eid in (final_state.get("execution_ids") or [])]
            output = final_state.get("final_result")
            if not isinstance(output, dict):
                output = {"result": output}

            error_code = final_state.get("error_code")
            error_message = final_state.get("error_message")

            wf_result = WorkflowResult(
                workflow_execution_id=workflow_execution_id,
                workflow_id=definition.workflow_id,
                workflow_version=definition.version,
                status=final_status.value,
                output=output,
                evidence=validated_evidence,
                execution_ids=exec_ids,
                warnings=warnings,
                failed_optional_steps=failed_optional,
                error_code=str(error_code) if error_code else None,
                error_message=sanitize_error_message(str(error_message)) if error_message else None,
                schema_version=definition.output_schema_version,
            )

            done_record = await self.repository.mark_completed(
                workflow_execution_id,
                context.tenant_id,
                status=final_status,
                result=wf_result,
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_code=wf_result.error_code,
                error_message=wf_result.error_message,
                warnings=warnings,
            )
            self.observer.record_event(
                f"workflow.{final_status.value.lower()}",
                record=done_record,
                details={"agents_invoked": len(exec_ids), "warnings_count": len(warnings)},
            )
            return done_record

        except TimeoutError:
            completed_at = datetime.now(UTC)
            duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))
            err = WorkflowTimeoutError(workflow_execution_id, timeout_seconds)
            failed = await self.repository.mark_completed(
                workflow_execution_id,
                context.tenant_id,
                status=WorkflowStatus.TIMED_OUT,
                result=None,
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_code=err.code.value,
                error_message=str(err),
            )
            self.observer.record_event("workflow.timed_out", record=failed)
            return failed

        except (WorkflowCancelledError, asyncio.CancelledError):
            completed_at = datetime.now(UTC)
            duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))
            cancelled = await self.repository.mark_completed(
                workflow_execution_id,
                context.tenant_id,
                status=WorkflowStatus.CANCELLED,
                result=None,
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_code=AgentErrorCode.WORKFLOW_CANCELLED.value,
                error_message=f"Workflow '{workflow_execution_id}' was cancelled.",
            )
            self.observer.record_event("workflow.cancelled", record=cancelled)
            return cancelled

        except AgentLayerError as exc:
            completed_at = datetime.now(UTC)
            duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))
            failed = await self.repository.mark_completed(
                workflow_execution_id,
                context.tenant_id,
                status=WorkflowStatus.FAILED,
                result=None,
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_code=exc.code.value,
                error_message=str(exc),
            )
            self.observer.record_event(
                "workflow.failed",
                record=failed,
                details={"error_code": exc.code.value},
            )
            return failed

        except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
            completed_at = datetime.now(UTC)
            duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))
            sanitized = sanitize_error_message(str(exc))
            failed = await self.repository.mark_completed(
                workflow_execution_id,
                context.tenant_id,
                status=WorkflowStatus.FAILED,
                result=None,
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_code=AgentErrorCode.WORKFLOW_STEP_FAILED.value,
                error_message=sanitized,
            )
            self.observer.record_event("workflow.failed", record=failed)
            return failed

        finally:
            self._cancel_flags.discard(workflow_execution_id)
            if slot_acquired and hasattr(self.workflow_policy, "release_slot"):
                self.workflow_policy.release_slot(context.tenant_id, workflow_execution_id)

    # ------------------------------------------------------------------
    # Query, Steps, Cancellation & Checkpoint Resume
    # ------------------------------------------------------------------

    async def get_workflow_execution(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> WorkflowExecutionRecord:
        self.security_policy.verify_trusted_context(context)
        record = await self.repository.get(workflow_execution_id, context.tenant_id)
        if record is None:
            raise WorkflowExecutionNotFoundError(workflow_execution_id)
        return record

    async def list_workflow_executions(
        self,
        context: AgentContext,
        *,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowExecutionRecord]:
        self.security_policy.verify_trusted_context(context)
        return await self.repository.list_executions(
            context.tenant_id,
            workflow_id=workflow_id,
            status=status,
            limit=limit,
        )

    async def get_workflow_result(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> WorkflowResult:
        record = await self.get_workflow_execution(workflow_execution_id, context)
        if record.status not in TERMINAL_WORKFLOW_STATUSES:
            raise WorkflowResultNotReadyError(workflow_execution_id, record.status.value)
        if record.result is not None:
            return record.result
        return WorkflowResult(
            workflow_execution_id=record.workflow_execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            status=record.status.value,
            output={},
            evidence=[],
            execution_ids=list(record.execution_ids),
            warnings=list(record.warnings),
            error_code=record.error_code,
            error_message=record.error_message,
        )

    async def get_workflow_steps(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> list[WorkflowStepLink]:
        await self.get_workflow_execution(workflow_execution_id, context)
        return await self.repository.list_steps(workflow_execution_id, context.tenant_id)

    async def cancel_workflow(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> WorkflowExecutionRecord:
        self.security_policy.verify_trusted_context(context)
        self._cancel_flags.add(workflow_execution_id)

        updated = await self.repository.request_cancel(
            workflow_execution_id,
            context.tenant_id,
            cancelled_at=datetime.now(UTC),
        )
        self.observer.record_event("workflow.cancel_requested", record=updated)

        # Propagate cooperative cancellation to any active Phase 4.2 child executions
        steps = await self.repository.list_steps(workflow_execution_id, context.tenant_id)
        for step in steps:
            if step.status in ("PENDING", "QUEUED", "RUNNING") and hasattr(
                self.runtime, "cancel_execution"
            ):
                try:
                    await self.runtime.cancel_execution(step.agent_execution_id, context)
                except AgentLayerError:
                    pass

        active_task = self._active_tasks.get(workflow_execution_id)
        if active_task is not None and not active_task.done():
            active_task.cancel()

        return updated

    async def resume_workflow(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> WorkflowExecutionRecord:
        """Safely resumes a failed/timed-out/interrupted workflow from checkpoint after re-authorization."""
        self.security_policy.verify_trusted_context(context)
        record = await self.get_workflow_execution(workflow_execution_id, context)

        if record.status in (
            WorkflowStatus.SUCCEEDED,
            WorkflowStatus.PARTIALLY_SUCCEEDED,
            WorkflowStatus.CANCELLED,
        ):
            raise WorkflowRecoveryNotAllowedError(
                workflow_execution_id,
                f"Workflow already finished with status {record.status.value}.",
            )

        # Re-authorize current caller permissions before resuming (ADR-076)
        definition = self.workflow_registry.get_definition(
            record.workflow_id,
            version=record.workflow_version,
            allow_disabled=True,
        )
        if self.workflow_policy is not None:
            self.workflow_policy.authorize_resume(definition, record, context)
        elif not self.permission_evaluator.can_invoke_agent(context):
            raise AgentAuthorizationError(
                "Caller permissions no longer permit resuming this workflow.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

        # Prevent blind replay of non-idempotent side-effecting steps
        prior_steps = await self.repository.list_steps(workflow_execution_id, context.tenant_id)
        unsafe_steps = [s.node_name for s in prior_steps if s.is_side_effecting and s.status != "SUCCEEDED"]
        if unsafe_steps:
            raise WorkflowRecoveryNotAllowedError(
                workflow_execution_id,
                f"Cannot safely replay non-idempotent side-effecting step(s): {', '.join(unsafe_steps)}.",
            )

        completed_nodes: set[str] = {s.node_name for s in prior_steps if s.status == "SUCCEEDED"}
        resume_state: dict[str, Any] | None = None

        if self.checkpoint_store is not None:
            latest_chk = await self.checkpoint_store.get_latest_workflow_checkpoint(
                workflow_execution_id=workflow_execution_id,
                context=context,
            )
            if latest_chk is not None:
                resume_state = dict(latest_chk.state)
                for node in resume_state.get("completed_nodes", []):
                    completed_nodes.add(str(node))

        return await self.execute_existing(
            workflow_execution_id,
            context,
            resume_state=resume_state,
            completed_nodes=completed_nodes,
            allow_from_recoverable=True,
        )

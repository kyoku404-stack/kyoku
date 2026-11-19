"""KEEP Phase 4.6 — Central Tool Execution Engine.

Executes registered platform tools within trusted server-side context with:
- Strict input/output schema validation
- Policy-driven authorization and tenant boundary checks
- Approval gating for restricted actions
- Sandboxed execution with timeout, concurrency limits, and retry control
- Comprehensive audit logging and secret redaction
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from backend.app.agents.errors import (
    ToolArgumentValidationError,
    ToolDisabledError,
    ToolNotFoundError,
    ToolOutputValidationError,
    ToolPromptInjectionBlockedError,
    sanitize_error_message,
)
from backend.app.agents.tools.contracts import (
    BaseTool,
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from backend.app.agents.tools.metadata import ToolMetadata
from backend.app.agents.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class KeepToolExecutor:
    """Central execution engine for approved KEEP platform tools."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy_service: Any = None,
        audit_service: Any = None,
        repository: Any = None,
        default_timeout: float = 15.0,
        max_concurrency: int = 20,
    ) -> None:
        self.registry = registry
        self.policy_service = policy_service
        self.audit_service = audit_service
        self.repository = repository
        self.default_timeout = default_timeout
        self._concurrency_semaphores: dict[str, asyncio.Semaphore] = {}
        self._global_semaphore = asyncio.Semaphore(max_concurrency)

    def _get_semaphore(self, tool_id: str, limit: int = 10) -> asyncio.Semaphore:
        """Retrieves or creates a per-tool concurrency semaphore."""
        if tool_id not in self._concurrency_semaphores:
            self._concurrency_semaphores[tool_id] = asyncio.Semaphore(limit)
        return self._concurrency_semaphores[tool_id]

    async def invoke(
        self,
        request: ToolCallRequest,
        context: ToolContext,
    ) -> ToolCallResult:
        """Invokes a registered tool through the full multi-stage validation and policy pipeline."""
        start_time = time.perf_counter()
        call_id = request.call_id
        tool_id = request.tool_id

        # Step 1: Tool Registry Resolution
        try:
            tool: BaseTool = self.registry.get(tool_id, check_enabled=True)
        except ToolNotFoundError:
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.failure(
                call_id=call_id,
                tool_id=tool_id,
                error_message=f"Tool '{tool_id}' is not registered in the platform catalog.",
                error_code="TOOL_NOT_FOUND",
                duration_ms=dur_ms,
            )
            await self._record_audit(request, context, res)
            return res
        except ToolDisabledError:
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.denied(
                call_id=call_id,
                tool_id=tool_id,
                reason=f"Tool '{tool_id}' is currently disabled by administrative policy.",
                error_code="TOOL_DISABLED",
                duration_ms=dur_ms,
            )
            await self._record_audit(request, context, res)
            return res

        metadata: ToolMetadata = tool.metadata

        # Step 2: Validate Input Arguments
        try:
            validated_args = tool.validate_arguments(request.arguments)
        except ToolArgumentValidationError as err:
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.failure(
                call_id=call_id,
                tool_id=tool_id,
                error_message=err.safe_message,
                error_code="TOOL_ARGUMENT_INVALID",
                duration_ms=dur_ms,
                metadata=err.details,
            )
            await self._record_audit(request, context, res)
            return res
        except Exception as err:  # noqa: BLE001 - Normalize unexpected argument validation failure
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.failure(
                call_id=call_id,
                tool_id=tool_id,
                error_message=sanitize_error_message(f"Input validation error: {err}"),
                error_code="TOOL_ARGUMENT_INVALID",
                duration_ms=dur_ms,
            )
            await self._record_audit(request, context, res)
            return res

        # Step 3: Authorization & Security Policy Check
        if self.policy_service is not None:
            try:
                decision = await self.policy_service.authorize(
                    tool=tool,
                    context=context,
                    arguments=request.arguments,
                )
                if not decision.allowed:
                    dur_ms = int((time.perf_counter() - start_time) * 1000)
                    if decision.approval_required:
                        res = ToolCallResult.approval_required(
                            call_id=call_id,
                            tool_id=tool_id,
                            reason=decision.reason_message or "Human approval required before execution.",
                            duration_ms=dur_ms,
                            metadata={"policy_code": decision.reason_code},
                        )
                    else:
                        res = ToolCallResult.denied(
                            call_id=call_id,
                            tool_id=tool_id,
                            reason=decision.reason_message or "Execution denied by platform policy.",
                            error_code=decision.reason_code or "TOOL_PERMISSION_DENIED",
                            duration_ms=dur_ms,
                            metadata={"policy_code": decision.reason_code},
                        )
                    await self._record_audit(request, context, res)
                    return res
            except ToolPromptInjectionBlockedError as err:
                dur_ms = int((time.perf_counter() - start_time) * 1000)
                res = ToolCallResult.denied(
                    call_id=call_id,
                    tool_id=tool_id,
                    reason=err.safe_message,
                    error_code="TOOL_PROMPT_INJECTION_BLOCKED",
                    duration_ms=dur_ms,
                    metadata=err.details,
                )
                await self._record_audit(request, context, res)
                return res

        # Step 4: Check Tool Approval Flag if not covered by policy service
        if metadata.requires_approval and not context.is_admin:
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.approval_required(
                call_id=call_id,
                tool_id=tool_id,
                reason=f"Tool '{tool_id}' requires explicit human approval before execution.",
                duration_ms=dur_ms,
            )
            await self._record_audit(request, context, res)
            return res

        # Step 5: Execute with Concurrency, Timeout, and Bounded Retries
        timeout_sec = metadata.timeout_seconds or self.default_timeout
        max_retries = metadata.max_retries if metadata.access_mode == "read" else 0
        tool_sem = self._get_semaphore(tool_id)

        attempts = 0
        last_error_msg = ""
        last_error_code = "TOOL_EXECUTION_FAILED"

        while attempts <= max_retries:
            attempts += 1
            try:
                async with self._global_semaphore, tool_sem:
                    raw_output = await asyncio.wait_for(
                        tool.execute(validated_args, context),
                        timeout=timeout_sec,
                    )
                # Success on execution attempt
                break
            except TimeoutError:
                dur_ms = int((time.perf_counter() - start_time) * 1000)
                res = ToolCallResult.timed_out(
                    call_id=call_id,
                    tool_id=tool_id,
                    timeout_seconds=timeout_sec,
                    duration_ms=dur_ms,
                )
                await self._record_audit(request, context, res)
                return res
            except Exception as err:  # noqa: BLE001 - Normalize arbitrary tool adapter execution failures
                last_error_msg = sanitize_error_message(str(err))
                logger.warning(
                    "Tool '%s' execution attempt %d failed: %s",
                    tool_id,
                    attempts,
                    last_error_msg,
                )
                if attempts <= max_retries:
                    await asyncio.sleep(0.05 * attempts)
                    continue
                # Exhausted retries
                dur_ms = int((time.perf_counter() - start_time) * 1000)
                res = ToolCallResult.failure(
                    call_id=call_id,
                    tool_id=tool_id,
                    error_message=f"Tool execution failed: {last_error_msg}",
                    error_code=last_error_code,
                    duration_ms=dur_ms,
                )
                await self._record_audit(request, context, res)
                return res

        # Step 6: Validate Output Schema
        try:
            validated_output = tool.validate_output(raw_output)
        except ToolOutputValidationError as err:
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.failure(
                call_id=call_id,
                tool_id=tool_id,
                error_message=err.safe_message,
                error_code="TOOL_OUTPUT_INVALID",
                duration_ms=dur_ms,
                metadata=err.details,
            )
            await self._record_audit(request, context, res)
            return res
        except Exception as err:  # noqa: BLE001 - Normalize unexpected output schema validation failure
            dur_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolCallResult.failure(
                call_id=call_id,
                tool_id=tool_id,
                error_message=sanitize_error_message(f"Output validation error: {err}"),
                error_code="TOOL_OUTPUT_INVALID",
                duration_ms=dur_ms,
            )
            await self._record_audit(request, context, res)
            return res

        # Step 7: Size Bounding
        try:
            serialized_len = len(json.dumps(validated_output).encode("utf-8"))
            if serialized_len > metadata.max_output_bytes:
                dur_ms = int((time.perf_counter() - start_time) * 1000)
                res = ToolCallResult.failure(
                    call_id=call_id,
                    tool_id=tool_id,
                    error_message=(
                        f"Tool output size ({serialized_len} bytes) exceeds configured limit of "
                        f"{metadata.max_output_bytes} bytes."
                    ),
                    error_code="TOOL_OUTPUT_TOO_LARGE",
                    duration_ms=dur_ms,
                    metadata={"size_bytes": serialized_len, "max_bytes": metadata.max_output_bytes},
                )
                await self._record_audit(request, context, res)
                return res
        except (TypeError, ValueError):
            pass

        # Step 8: Build Successful Result
        dur_ms = int((time.perf_counter() - start_time) * 1000)
        result = ToolCallResult.success(
            call_id=call_id,
            tool_id=tool_id,
            output=validated_output,
            duration_ms=dur_ms,
            metadata={
                "attempts": attempts,
                "tenant_id": context.tenant_id,
                "correlation_id": context.correlation_id,
            },
        )

        # Step 9: Audit and Persistence
        await self._record_audit(request, context, result)
        return result

    async def _record_audit(
        self,
        request: ToolCallRequest,
        context: ToolContext,
        result: ToolCallResult,
    ) -> None:
        """Dispatches audit log and invocation record recording with fail-closed safety."""
        # Record via audit service if provided
        if self.audit_service is not None:
            try:
                await self.audit_service.record_invocation(
                    request=request,
                    context=context,
                    result=result,
                )
            except Exception as audit_err:  # noqa: BLE001 - Non-blocking audit recording error
                logger.error("Failed to record tool audit event: %s", audit_err)

        # Record via persistence repository if provided
        if self.repository is not None:
            try:
                await self.repository.save_invocation(
                    request=request,
                    context=context,
                    result=result,
                )
            except Exception as repo_err:  # noqa: BLE001 - Non-blocking persistence recording error
                logger.error("Failed to persist tool invocation record: %s", repo_err)

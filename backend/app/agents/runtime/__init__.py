"""KEEP Phase 4.2 — Agent Runtime & Execution Engine Package."""

from backend.app.agents.runtime.context import (
    RuntimeExecutionContext,
    build_runtime_context,
)
from backend.app.agents.runtime.executor import (
    AgentRuntime,
    compute_request_fingerprint,
)
from backend.app.agents.runtime.interfaces import (
    AgentRuntimeInterface,
    BackgroundDispatcher,
    ExecutionPolicyInterface,
    ExecutionRepository,
    RuntimeObserver,
)
from backend.app.agents.runtime.lifecycle import (
    ACTIVE_STATUSES,
    ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
    ExecutionMode,
    ExecutionRecord,
    ExecutionStatus,
    assert_valid_transition,
    can_transition,
    generate_execution_id,
    is_terminal_status,
)

__all__ = [
    "ACTIVE_STATUSES",
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATUSES",
    "AgentRuntime",
    "AgentRuntimeInterface",
    "BackgroundDispatcher",
    "ExecutionMode",
    "ExecutionPolicyInterface",
    "ExecutionRecord",
    "ExecutionRepository",
    "ExecutionStatus",
    "RuntimeExecutionContext",
    "RuntimeObserver",
    "assert_valid_transition",
    "build_runtime_context",
    "can_transition",
    "compute_request_fingerprint",
    "generate_execution_id",
    "is_terminal_status",
]

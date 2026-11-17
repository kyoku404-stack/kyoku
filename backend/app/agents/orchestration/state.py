"""KEEP Phase 4.3 — Typed Orchestration State Schema, Reducers & Validation.

Defines the structured state passed between graph nodes, explicit merge reducers
preventing parallel branch clobbering, intermediate output validation models, and
secret-safe checkpoint sanitization.

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Sections 5, 7, 8)
"""

from __future__ import annotations

from typing import Any, TypedDict

from backend.app.agents.contracts import EvidenceReference
from backend.app.agents.errors import sanitize_error_message
from pydantic import BaseModel, Field

STATE_VERSION = "1.0"

_SENSITIVE_KEY_TOKENS = ("password", "secret", "token", "api_key", "authorization", "credential")


class WorkflowState(TypedDict, total=False):
    """Typed orchestration state shared across sequential, conditional, and parallel nodes."""

    state_version: str
    workflow_id: str
    workflow_version: str
    workflow_execution_id: str
    tenant_id: str
    requested_by: str
    correlation_id: str
    goal: str
    input: dict[str, Any]
    research_result: dict[str, Any]
    analysis_result: dict[str, Any]
    branch_results: dict[str, dict[str, Any]]
    final_result: dict[str, Any]
    evidence: list[dict[str, Any]]
    execution_ids: list[str]
    warnings: list[str]
    failed_optional_steps: list[str]
    completed_nodes: list[str]
    workflow_status: str
    error_code: str | None
    error_message: str | None


class ValidatedRetrievalOutput(BaseModel):
    """Validated structured contract handed off from retrieval to downstream analysis nodes."""

    query: str = Field(..., min_length=1)
    topic: str = Field(default="general")
    document_count: int = Field(default=0, ge=0)
    summary: str = Field(default="")
    evidence: list[EvidenceReference] = Field(default_factory=list)


class ValidatedAnalysisOutput(BaseModel):
    """Validated structured contract produced by sequential analysis nodes."""

    summary: str = Field(..., min_length=1)
    key_findings: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    sources_used: int = Field(default=0, ge=0)


class ValidatedBranchOutput(BaseModel):
    """Validated structured contract produced by parallel specialist branch nodes."""

    branch_name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    items: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for raw in items:
        ev_dict = raw.model_dump(mode="json") if isinstance(raw, EvidenceReference) else dict(raw)
        key = (str(ev_dict.get("source_id", "")), str(ev_dict.get("source_type", "")))
        if key not in seen:
            seen.add(key)
            result.append(ev_dict)
    return result


def merge_workflow_state(
    base: dict[str, Any],
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Merges a node state update into `base` using explicit reducers safe for parallel fan-in."""
    merged = dict(base)
    for key, value in patch.items():
        if key in ("execution_ids", "failed_optional_steps", "completed_nodes"):
            existing = list(merged.get(key) or [])
            incoming = list(value or [])
            merged[key] = _dedupe_preserve_order([*existing, *[str(v) for v in incoming]])
        elif key == "warnings":
            existing_w = list(merged.get("warnings") or [])
            incoming_w = [str(w) for w in (value or [])]
            merged["warnings"] = [*existing_w, *incoming_w]
        elif key == "evidence":
            existing_ev = list(merged.get("evidence") or [])
            incoming_ev = list(value or [])
            merged["evidence"] = _dedupe_evidence([*existing_ev, *incoming_ev])
        elif key == "branch_results":
            existing_branches = dict(merged.get("branch_results") or {})
            incoming_branches = dict(value or {})
            existing_branches.update(incoming_branches)
            merged["branch_results"] = existing_branches
        else:
            merged[key] = value
    return merged


def sanitize_checkpoint_state(state: dict[str, Any]) -> dict[str, Any]:
    """Removes sensitive keys and redacts secrets prior to persisting graph checkpoints."""

    def _clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            cleaned: dict[str, Any] = {}
            for k, v in obj.items():
                lower_k = str(k).lower()
                if any(tok in lower_k for tok in _SENSITIVE_KEY_TOKENS):
                    cleaned[k] = "[REDACTED]"
                else:
                    cleaned[k] = _clean(v)
            return cleaned
        if isinstance(obj, list):
            return [_clean(item) for item in obj]
        if isinstance(obj, str):
            return sanitize_error_message(obj, max_length=2000)
        return obj

    return _clean(state)

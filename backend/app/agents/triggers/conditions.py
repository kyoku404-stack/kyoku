"""KEEP Phase 4.10 — Safe Declarative Trigger Condition Evaluator.

Evaluates declarative filters against event payload and envelope fields using an
explicitly allowlisted operator set. Never calls `eval()` or `exec()`.

Supported condition forms:
- Scalar equality shorthand: `{"collection_id": "collection-10"}`
- Operator objects: `{"severity": {"in": ["high", "critical"]}}`
- Supported operators: `eq`, `neq`, `in`, `not_in`, `contains`, `gt`, `gte`, `lt`, `lte`, `exists`

Owner: Member 2 (Trigger Registry & Rule Engine)
Specification: devdocs/p4/p4.10.txt (Section 6)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.errors import EventValidationError
from backend.app.agents.events.contracts import KeepEvent

ALLOWED_CONDITION_OPERATORS: frozenset[str] = frozenset(
    {"eq", "neq", "in", "not_in", "contains", "gt", "gte", "lt", "lte", "exists"}
)


def validate_condition_spec(conditions: dict[str, Any]) -> None:
    """Validates condition syntax strictly against the allowlisted operator set."""
    if not isinstance(conditions, dict):
        raise EventValidationError("Trigger conditions must be a JSON object.")
    for field_path, rule in conditions.items():
        if not isinstance(field_path, str) or not field_path.strip():
            raise EventValidationError("Condition field path must be a non-empty string.")
        if isinstance(rule, dict):
            if not rule:
                raise EventValidationError(f"Condition operator map for '{field_path}' cannot be empty.")
            for op in rule:
                if op not in ALLOWED_CONDITION_OPERATORS:
                    raise EventValidationError(
                        f"Unsupported trigger condition operator '{op}' (allowed: {sorted(ALLOWED_CONDITION_OPERATORS)})."
                    )


def _resolve_field(event: KeepEvent, field_path: str) -> tuple[bool, Any]:
    """Resolves dotted path from event payload first, falling back to envelope metadata."""
    if field_path in ("event_type", "source", "resource_id", "schema_version"):
        return True, getattr(event, field_path)

    parts = field_path.split(".")
    current: Any = event.payload
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def _apply_operator(op: str, actual: Any, expected: Any, exists: bool) -> bool:
    if op == "exists":
        return exists is bool(expected)
    if not exists:
        return op == "neq"
    if op == "eq":
        return bool(actual == expected)
    if op == "neq":
        return bool(actual != expected)
    if op == "in":
        return bool(isinstance(expected, (list, tuple, set)) and actual in expected)
    if op == "not_in":
        return bool(isinstance(expected, (list, tuple, set)) and actual not in expected)
    if op == "contains":
        if isinstance(actual, (str, list, tuple)):
            return bool(expected in actual)
        return False
    if op in ("gt", "gte", "lt", "lte"):
        try:
            a_num = float(actual)
            b_num = float(expected)
        except (TypeError, ValueError):
            return False
        if op == "gt":
            return a_num > b_num
        if op == "gte":
            return a_num >= b_num
        if op == "lt":
            return a_num < b_num
        return a_num <= b_num
    return False


def evaluate_conditions(event: KeepEvent, conditions: dict[str, Any]) -> tuple[bool, str]:
    """Evaluates all declared conditions with logical AND semantics."""
    if not conditions:
        return True, "No filter conditions; matches all events of this type."

    for field_path, rule in conditions.items():
        exists, actual = _resolve_field(event, field_path)
        if isinstance(rule, dict):
            for op, expected in rule.items():
                if not _apply_operator(op, actual, expected, exists):
                    return False, f"Condition mismatch on '{field_path}' ({op} {expected!r})."
        else:
            if not exists or actual != rule:
                return False, f"Condition mismatch on '{field_path}' == {rule!r}."
    return True, "All declarative trigger conditions matched."

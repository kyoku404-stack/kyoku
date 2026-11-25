"""Phase 4.11 — Evidence & Provenance Validation Service."""

from __future__ import annotations

from collections.abc import Callable

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
    IntelligenceSecurityContext,
)


class EvidenceValidator:
    """Validates candidate evidence references against authorized KEEP sources.

    - Separates missing evidence into explicit `limitations` instead of fabricating conclusions.
    - Enforces `accessible_resource_refs` when provided in the security context.
    """

    def __init__(
        self,
        resource_exists_fn: Callable[[str, str], bool] | None = None,
    ) -> None:
        self._resource_exists_fn = resource_exists_fn

    async def validate(
        self,
        candidate: IntelligenceCandidate,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, list[EvidenceReference], list[str]]:
        limitations = list(candidate.limitations)
        records: list[EvidenceReference] = []

        raw_records = list(candidate.evidence_details)
        existing_refs = {r.resource_ref for r in raw_records}
        for ref in candidate.evidence_refs:
            if ref not in existing_refs:
                raw_records.append(EvidenceReference(resource_ref=ref, source_type="document"))

        allowed_set = (
            set(ctx.accessible_resource_refs)
            if ctx.accessible_resource_refs is not None
            else None
        )

        valid_count = 0
        for rec in raw_records:
            outcome = rec.validation_outcome
            if allowed_set is not None and rec.resource_ref not in allowed_set:
                outcome = "unauthorized"
                limitations.append(f"Caller lacks access to evidence '{rec.resource_ref}'.")
            elif self._resource_exists_fn is not None and not self._resource_exists_fn(
                ctx.tenant_id, rec.resource_ref
            ):
                outcome = "missing"
                limitations.append(f"Referenced source '{rec.resource_ref}' could not be resolved.")
            else:
                valid_count += 1

            records.append(
                rec.model_copy(
                    update={"validation_outcome": outcome},
                )
            )

        if valid_count == 0 and not candidate.allow_evidence_free:
            if not records:
                limitations.append("No verifiable supporting evidence references provided.")
            return False, records, list(dict.fromkeys(limitations))

        return True, records, list(dict.fromkeys(limitations))

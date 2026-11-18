"""KEEP Phase 4.4 — Capability-Based Agent Selector.

Matches every `PlannedTask.required_capabilities` strictly against enabled agents
in KEEP's real Phase 4.1 `AgentRegistry`, ignoring any LLM-guessed agent names and
emitting structured findings when capabilities are unavailable or disabled (ADR-078).

Owner: Member 3 (Agent Selection, Policies & Plan Validation)
Specification: devdocs/p4/p4.4.txt (Sections 1, 3, 8)
"""

from __future__ import annotations

from backend.app.agents.contracts import AgentContext
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    PlannedTask,
    ValidationFinding,
    ValidationSeverity,
)
from backend.app.agents.registry import AgentRegistry


class CapabilityAgentSelector:
    """Resolves planned task capabilities against KEEP's live Phase 4.1 AgentRegistry."""

    def __init__(self, agent_registry: AgentRegistry) -> None:
        self.agent_registry = agent_registry

    def list_available_capabilities(self) -> list[str]:
        """Returns sorted unique capability names offered by currently enabled registered agents."""
        caps: set[str] = set()
        for item in self.agent_registry.list_agents(include_disabled=False):
            for cap in item.get("capabilities", []):
                name = cap.get("name") if isinstance(cap, dict) else getattr(cap, "name", None)
                if name:
                    caps.add(str(name))
        return sorted(caps)

    def _find_best_agent(self, required_capabilities: list[str]) -> AgentMetadata | None:
        """Selects the most specific enabled agent whose capabilities cover `required_capabilities`."""
        needed = {c.strip().lower() for c in required_capabilities if c.strip()}
        if not needed:
            return None

        candidates: list[tuple[int, str, AgentMetadata]] = []
        for item in self.agent_registry.list_agents(include_disabled=False):
            agent_id = str(item["agent_id"])
            meta = self.agent_registry.get_metadata(agent_id)
            if not meta.enabled:
                continue
            offered = {cap.name.strip().lower() for cap in meta.capabilities}
            if needed.issubset(offered):
                # Prefer specialist agents with fewer extra capabilities, tie-break deterministically
                candidates.append((len(offered), meta.agent_id, meta))

        if not candidates:
            return None
        candidates.sort(key=lambda tup: (tup[0], tup[1]))
        return candidates[0][2]

    async def resolve(
        self,
        plan: ExecutionPlan,
        *,
        context: AgentContext,
    ) -> tuple[ExecutionPlan, list[ValidationFinding]]:
        """Resolves every task to a real registered agent ID + version or emits structured findings."""
        _ = context  # Reserved for future tenant-scoped agent catalogs
        findings: list[ValidationFinding] = []
        resolved_tasks: list[PlannedTask] = []

        for task in plan.tasks:
            matched = self._find_best_agent(task.required_capabilities)
            if matched is None:
                severity = ValidationSeverity.ERROR if task.required else ValidationSeverity.WARNING
                findings.append(
                    ValidationFinding(
                        code="PLAN_CAPABILITY_UNAVAILABLE",
                        check="capability_resolution",
                        severity=severity,
                        message=(
                            f"No enabled registered agent satisfies required capabilities "
                            f"{task.required_capabilities} for task '{task.task_id}'."
                        ),
                        task_id=task.task_id,
                        details={"required_capabilities": list(task.required_capabilities)},
                    )
                )
                resolved_tasks.append(
                    task.model_copy(
                        update={"resolved_agent_id": None, "resolved_agent_version": None}
                    )
                )
            else:
                resolved_tasks.append(
                    task.model_copy(
                        update={
                            "resolved_agent_id": matched.agent_id,
                            "resolved_agent_version": matched.version,
                        }
                    )
                )

        resolved_plan = plan.model_copy(update={"tasks": resolved_tasks})
        return resolved_plan, findings

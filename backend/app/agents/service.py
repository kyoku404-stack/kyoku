"""KEEP Phase 4.1 — KeepAgentService Facade & Default Registry Factory.

Coordinates `AgentRegistry` lookup, `KeepAgentPolicyEngine` authorization,
and `BaseAgent` invocation so FastAPI routes and Phase 4.2 runtime callers
share a single policy-enforced entry point.

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Sections 2, 5, 9)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentContractValidationError,
    AgentErrorCode,
    AgentLayerError,
)
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.reference_agent import ReferenceAgent
from backend.app.agents.registry import AgentRegistry
from backend.app.services.security.agent_permissions import AgentPermissionEvaluator
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)


def build_default_agent_registry() -> AgentRegistry:
    """Initializes a fresh AgentRegistry populated with KEEP's Phase 4.1 ReferenceAgent."""
    registry = AgentRegistry()
    registry.register(ReferenceAgent())
    return registry


class KeepAgentService:
    """Policy-enforced service facade over KEEP's AgentRegistry and BaseAgent contracts."""

    def __init__(
        self,
        registry: AgentRegistry,
        *,
        policy: AgentPolicyInterface | None = None,
        permission_evaluator: AgentPermissionEvaluator | None = None,
    ) -> None:
        self.registry = registry
        self.permission_evaluator = permission_evaluator or AgentPermissionEvaluator()
        self.policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine(
            permission_evaluator=self.permission_evaluator
        )

    def list_agents(
        self,
        context: AgentContext,
        *,
        include_disabled: bool = False,
        capability: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lists discoverable agents; restricts disabled-agent visibility to admins."""
        self.policy.verify_trusted_context(context)
        can_see_disabled = (
            include_disabled and self.permission_evaluator.can_view_disabled_agents(context)
        )
        return self.registry.list_agents(
            include_disabled=can_see_disabled,
            capability=capability,
        )

    def get_agent_metadata(
        self,
        agent_id: str,
        context: AgentContext,
    ) -> AgentMetadata:
        """Inspects metadata for a single agent; blocks non-admins from viewing disabled agents."""
        self.policy.verify_trusted_context(context)
        metadata = self.registry.get_metadata(agent_id)
        if not metadata.enabled and not self.permission_evaluator.can_view_disabled_agents(context):
            raise AgentAuthorizationError(
                f"Caller is not authorized to inspect disabled agent '{metadata.agent_id}'.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )
        return metadata

    def set_agent_enabled(
        self,
        agent_id: str,
        enabled: bool,
        context: AgentContext,
    ) -> AgentMetadata:
        """Admin-only toggle for enabling or disabling a registered agent."""
        self.policy.verify_trusted_context(context)
        if not self.permission_evaluator.can_manage_agents(context):
            raise AgentAuthorizationError(
                "Only OrgAdmin or SuperAdmin may enable or disable agents.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )
        return self.registry.set_enabled(agent_id, enabled)

    async def invoke_agent(
        self,
        agent_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Validates registry status, enforces security policy, invokes agent, and validates result."""
        self.policy.verify_trusted_context(context)
        agent = self.registry.get(agent_id)
        metadata = self.registry.get_metadata(agent_id)

        # Enforce capability, tenant, spoofed-identity, and prompt-injection policies
        self.policy.authorize_invocation(metadata, request, context)

        # Propagate trusted correlation_id when caller omitted one
        effective_request = (
            request
            if request.correlation_id
            else request.model_copy(update={"correlation_id": context.correlation_id})
        )

        try:
            result = await agent.invoke(effective_request, context)
        except AgentLayerError:
            raise
        except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message=f"Agent '{metadata.agent_id}' encountered an execution error: {exc}",
            )

        if not isinstance(result, AgentResult):
            raise AgentContractValidationError(
                f"Agent '{metadata.agent_id}' returned invalid result type '{type(result).__name__}'."
            )

        return AgentResult.model_validate(result.model_dump())

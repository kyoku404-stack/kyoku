"""Abstract Interfaces and Contracts for AI / LLM, Embedding Providers, Prompts & Context.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/ai
Specification: devdocs/p1/p1.2.txt (Chapters 10, 11, 16, 17, 19)
             devdocs/p1/p1.6.txt (Chapters 3-14, 18) — Phase 1.6 Authorization Framework
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class MessageRole(str, Enum):
    """Supported roles in conversational LLM interactions."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class UserRole(str, Enum):
    """Supported organizational roles within KEEP (Phase 1.4 RBAC)."""

    SUPER_ADMIN = "SuperAdmin"
    ORGANIZATION_ADMIN = "OrgAdmin"
    PROJECT_MANAGER = "ProjectManager"
    EMPLOYEE = "Member"
    VIEWER = "Viewer"


class AIPermission(str, Enum):
    """Granular permissions governing AI, search, and knowledge operations."""

    CHAT_QUERY = "chat:query"
    CHAT_STREAM = "chat:stream"
    CHAT_HISTORY = "chat:history"
    CHAT_MANAGE_ALL = "chat:manage_all"
    SEARCH_QUERY = "search:query"
    DOC_READ = "doc:read"
    DOC_CREATE = "doc:create"
    DOC_UPDATE = "doc:update"
    DOC_DELETE = "doc:delete"
    KG_READ = "kg:read"
    KG_WRITE = "kg:write"
    TOOL_EXECUTE = "tool:execute"
    ANALYTICS_READ = "analytics:read"
    USERS_MANAGE = "users:manage"
    ORG_MANAGE = "org:manage"

    # Phase 1.5 Organization, Workspace & Hierarchy Governance
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_SETTINGS = "org:settings"
    DEPT_CREATE = "dept:create"
    DEPT_READ = "dept:read"
    DEPT_UPDATE = "dept:update"
    DEPT_DELETE = "dept:delete"
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MEMBERSHIP = "project:membership"
    INVITATION_CREATE = "invitation:create"
    INVITATION_READ = "invitation:read"
    INVITATION_REVOKE = "invitation:revoke"
    MEMBER_READ = "member:read"
    MEMBER_UPDATE = "member:update"
    MEMBER_REMOVE = "member:remove"

    # Phase 1.6 Resource-Level Authorization & Policy Engine
    DOCUMENT_CREATE = "document.create"
    DOCUMENT_READ = "document.read"
    DOCUMENT_UPDATE = "document.update"
    DOCUMENT_DELETE = "document.delete"
    PROJECT_MANAGE = "project.manage"
    MEETING_CREATE = "meeting.create"
    MEETING_READ = "meeting.read"
    MEETING_MANAGE = "meeting.manage"
    AI_CHAT = "ai.chat"
    AI_SEARCH = "ai.search"
    AI_ADMIN = "ai.admin"
    AI_CONFIG = "ai.config"
    ORGANIZATION_MANAGE = "organization.manage"
    ORGANIZATION_SETTINGS = "organization.settings"
    USER_INVITE = "user.invite"
    USER_MANAGE = "user.manage"
    USER_VIEW = "user.view"
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    AUDIT_READ = "audit.read"
    ORGANIZATION_CREATE = "organization.create"
    PROJECT_CREATE_ACTION = "project.create"

    # Phase 1.8 Document Management & File Storage System
    DOCUMENT_DOWNLOAD = "document.download"
    DOCUMENT_PREVIEW = "document.preview"
    DOCUMENT_VERSION = "document.version"

    # Phase 2.4 Knowledge Graph & Enterprise Intelligence
    GRAPH_READ = "graph.read"
    GRAPH_BUILD = "graph.build"
    GRAPH_INTELLIGENCE = "graph.intelligence"

    # Phase 3.1 Enterprise Integrations & Connector Framework
    CONNECTOR_VIEW = "connector.view"
    CONNECTOR_MANAGE = "connector.manage"
    CONNECTOR_SYNC = "connector.sync"

    # Phase 3.2 Real-Time Collaboration, Team Workspaces & Knowledge Sharing
    WORKSPACE_VIEW = "workspace.view"
    WORKSPACE_MANAGE = "workspace.manage"
    WORKSPACE_CREATE = "workspace.create"
    COMMENT_CREATE = "comment.create"
    COMMENT_RESOLVE = "comment.resolve"
    VERSION_HISTORY_VIEW = "version.view"
    PRESENCE_UPDATE = "presence.update"

    # Phase 3.3 Enterprise Security, Compliance, Governance & Data Protection
    SECURITY_VIEW = "security.view"
    SECURITY_MANAGE = "security.manage"
    SECURITY_AUDIT = "security.audit"
    SECURITY_COMPLIANCE = "security.compliance"
    DATA_CLASSIFY = "data.classify"

    # Phase 3.4 Workflow Automation, Notifications & Event-Driven Intelligence
    WORKFLOW_VIEW = "workflow.view"
    WORKFLOW_MANAGE = "workflow.manage"
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_APPROVE = "workflow.approve"
    NOTIFICATION_VIEW = "notification.view"
    NOTIFICATION_MANAGE = "notification.manage"

    # Phase 3.5 Plugin SDK, Extension Framework & Developer Ecosystem
    PLUGIN_VIEW = "plugin.view"
    PLUGIN_MANAGE = "plugin.manage"
    PLUGIN_INSTALL = "plugin.install"
    PLUGIN_EXECUTE = "plugin.execute"


# Hierarchical Permission Mapping (Higher roles inherit lower permissions)
VIEWER_PERMISSIONS: set[str] = {
    AIPermission.SEARCH_QUERY.value,
    AIPermission.DOC_READ.value,
    AIPermission.KG_READ.value,
    AIPermission.ORG_READ.value,
    AIPermission.DEPT_READ.value,
    AIPermission.TEAM_READ.value,
    AIPermission.PROJECT_READ.value,
    AIPermission.MEMBER_READ.value,
    # Phase 1.6 action-based permissions
    AIPermission.DOCUMENT_READ.value,
    AIPermission.MEETING_READ.value,
    AIPermission.AI_CHAT.value,
    AIPermission.AI_SEARCH.value,
    AIPermission.USER_VIEW.value,
    AIPermission.ANALYTICS_VIEW.value,
    # Phase 1.8 document permissions
    AIPermission.DOCUMENT_DOWNLOAD.value,
    AIPermission.DOCUMENT_PREVIEW.value,
    # Phase 2.4 graph permissions
    AIPermission.GRAPH_READ.value,
    # Phase 3.1 connector permissions
    AIPermission.CONNECTOR_VIEW.value,
    # Phase 3.2 collaboration permissions
    AIPermission.WORKSPACE_VIEW.value,
    AIPermission.VERSION_HISTORY_VIEW.value,
    AIPermission.PRESENCE_UPDATE.value,
    # Phase 3.3 security permissions
    AIPermission.SECURITY_VIEW.value,
    # Phase 3.4 workflow permissions
    AIPermission.WORKFLOW_VIEW.value,
    AIPermission.NOTIFICATION_VIEW.value,
    # Phase 3.5 plugin permissions
    AIPermission.PLUGIN_VIEW.value,
}

EMPLOYEE_PERMISSIONS: set[str] = VIEWER_PERMISSIONS | {
    AIPermission.CHAT_QUERY.value,
    AIPermission.CHAT_STREAM.value,
    AIPermission.CHAT_HISTORY.value,
    AIPermission.DOC_CREATE.value,
    AIPermission.DOC_UPDATE.value,
    AIPermission.TOOL_EXECUTE.value,
    AIPermission.PROJECT_CREATE.value,
    AIPermission.PROJECT_UPDATE.value,
    AIPermission.INVITATION_READ.value,
    # Phase 1.6 action-based permissions
    AIPermission.DOCUMENT_CREATE.value,
    AIPermission.DOCUMENT_UPDATE.value,
    AIPermission.PROJECT_CREATE_ACTION.value,
    # Phase 1.8 document permissions
    AIPermission.DOCUMENT_VERSION.value,
    # Phase 2.4 graph permissions
    AIPermission.GRAPH_INTELLIGENCE.value,
    # Phase 3.2 collaboration permissions
    AIPermission.WORKSPACE_CREATE.value,
    AIPermission.COMMENT_CREATE.value,
    # Phase 3.3 security permissions
    AIPermission.DATA_CLASSIFY.value,
    # Phase 3.4 workflow permissions
    AIPermission.NOTIFICATION_MANAGE.value,
    AIPermission.WORKFLOW_EXECUTE.value,
    # Phase 3.5 plugin permissions
    AIPermission.PLUGIN_EXECUTE.value,
}

PROJECT_MANAGER_PERMISSIONS: set[str] = EMPLOYEE_PERMISSIONS | {
    AIPermission.DOC_DELETE.value,
    AIPermission.KG_WRITE.value,
    AIPermission.TEAM_CREATE.value,
    AIPermission.TEAM_UPDATE.value,
    AIPermission.PROJECT_DELETE.value,
    AIPermission.PROJECT_MEMBERSHIP.value,
    AIPermission.INVITATION_CREATE.value,
    # Phase 1.6 action-based permissions
    AIPermission.DOCUMENT_DELETE.value,
    AIPermission.PROJECT_MANAGE.value,
    AIPermission.MEETING_CREATE.value,
    AIPermission.MEETING_MANAGE.value,
    AIPermission.USER_INVITE.value,
    # Phase 2.4 graph permissions
    AIPermission.GRAPH_BUILD.value,
    # Phase 3.1 connector permissions
    AIPermission.CONNECTOR_SYNC.value,
    # Phase 3.2 collaboration permissions
    AIPermission.COMMENT_RESOLVE.value,
    # Phase 3.4 workflow permissions
    AIPermission.WORKFLOW_APPROVE.value,
    # Phase 3.5 plugin permissions
    AIPermission.PLUGIN_INSTALL.value,
}

ORG_ADMIN_PERMISSIONS: set[str] = PROJECT_MANAGER_PERMISSIONS | {
    AIPermission.CHAT_MANAGE_ALL.value,
    AIPermission.ANALYTICS_READ.value,
    AIPermission.USERS_MANAGE.value,
    AIPermission.ORG_MANAGE.value,
    AIPermission.ORG_UPDATE.value,
    AIPermission.ORG_DELETE.value,
    AIPermission.ORG_SETTINGS.value,
    AIPermission.DEPT_CREATE.value,
    AIPermission.DEPT_UPDATE.value,
    AIPermission.DEPT_DELETE.value,
    AIPermission.TEAM_DELETE.value,
    AIPermission.INVITATION_REVOKE.value,
    AIPermission.MEMBER_UPDATE.value,
    AIPermission.MEMBER_REMOVE.value,
    # Phase 1.6 action-based permissions
    AIPermission.ORGANIZATION_MANAGE.value,
    AIPermission.ORGANIZATION_SETTINGS.value,
    AIPermission.USER_MANAGE.value,
    AIPermission.AI_ADMIN.value,
    AIPermission.AI_CONFIG.value,
    AIPermission.ANALYTICS_EXPORT.value,
    AIPermission.AUDIT_READ.value,
    # Phase 3.1 connector permissions
    AIPermission.CONNECTOR_MANAGE.value,
    # Phase 3.2 collaboration permissions
    AIPermission.WORKSPACE_MANAGE.value,
    # Phase 3.3 security permissions
    AIPermission.SECURITY_MANAGE.value,
    AIPermission.SECURITY_AUDIT.value,
    AIPermission.SECURITY_COMPLIANCE.value,
    # Phase 3.4 workflow permissions
    AIPermission.WORKFLOW_MANAGE.value,
    # Phase 3.5 plugin permissions
    AIPermission.PLUGIN_MANAGE.value,
}

SUPER_ADMIN_PERMISSIONS: set[str] = ORG_ADMIN_PERMISSIONS | {
    AIPermission.ORG_CREATE.value,
    AIPermission.ORGANIZATION_CREATE.value,
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    UserRole.VIEWER.value: VIEWER_PERMISSIONS,
    UserRole.EMPLOYEE.value: EMPLOYEE_PERMISSIONS,
    UserRole.PROJECT_MANAGER.value: PROJECT_MANAGER_PERMISSIONS,
    UserRole.ORGANIZATION_ADMIN.value: ORG_ADMIN_PERMISSIONS,
    UserRole.SUPER_ADMIN.value: SUPER_ADMIN_PERMISSIONS,
    "Viewer": VIEWER_PERMISSIONS,
    "Member": EMPLOYEE_PERMISSIONS,
    "ProjectManager": PROJECT_MANAGER_PERMISSIONS,
    "OrgAdmin": ORG_ADMIN_PERMISSIONS,
    "SuperAdmin": SUPER_ADMIN_PERMISSIONS,
}


# ---------------------------------------------------------------------------
# Phase 1.6 — Authorization Domain Contracts
# ---------------------------------------------------------------------------


class ResourceType(str, Enum):
    """Resource types subject to authorization policy evaluation."""

    DOCUMENT = "document"
    PROJECT = "project"
    TEAM = "team"
    DEPARTMENT = "department"
    MEETING = "meeting"
    CHAT_SESSION = "chat_session"
    AI_QUERY = "ai_query"
    ORGANIZATION = "organization"
    MEMBER = "member"
    INVITATION = "invitation"


@dataclass
class ResourceAuthorizationContext:
    """Full context for evaluating a single resource-level authorization decision.

    Combines caller identity (role, tenant, memberships) with target resource
    ownership and organizational metadata for policy engine evaluation.
    """

    # Caller identity
    caller_id: UUID
    caller_role: str
    caller_org_id: UUID
    caller_project_ids: set[UUID] = field(default_factory=set)
    caller_team_ids: set[UUID] = field(default_factory=set)
    caller_dept_id: UUID | None = None

    # Target resource metadata
    resource_id: UUID = field(default_factory=lambda: __import__('uuid').uuid4())
    resource_type: ResourceType = ResourceType.DOCUMENT
    resource_org_id: UUID = field(default_factory=lambda: __import__('uuid').uuid4())
    resource_owner_id: UUID | None = None
    resource_project_id: UUID | None = None
    required_permission: str = ""


@dataclass
class AuthorizationDecision:
    """Result of a policy engine authorization evaluation."""

    allowed: bool
    reason: str = ""
    error_code: str | None = None
    required_permission: str = ""
    resource_type: str = ""

    @classmethod
    def allow(cls, reason: str = "Permission granted") -> "AuthorizationDecision":
        """Constructs an ALLOW decision."""
        return cls(allowed=True, reason=reason)

    @classmethod
    def deny(
        cls,
        error_code: str,
        reason: str = "Permission denied",
        required_permission: str = "",
        resource_type: str = "",
    ) -> "AuthorizationDecision":
        """Constructs a DENY decision with a structured error code."""
        return cls(
            allowed=False,
            reason=reason,
            error_code=error_code,
            required_permission=required_permission,
            resource_type=resource_type,
        )


class BaseAuthorizationPolicyEngine(ABC):
    """Abstract interface for centralized authorization policy evaluation.

    Implements the 7-step authorization pipeline defined in
    docs/Architecture/authorization-architecture.md Section 2:
    tenant boundary -> permission check -> ownership override -> project membership.
    """

    @abstractmethod
    def evaluate_access(
        self,
        context: ResourceAuthorizationContext,
    ) -> AuthorizationDecision:
        """Evaluates all authorization rules for a single resource access request.

        Args:
            context: Full caller identity + resource metadata context.

        Returns:
            AuthorizationDecision with allowed flag, reason, and error_code.
        """

    @abstractmethod
    def evaluate_bulk_access(
        self,
        contexts: list[ResourceAuthorizationContext],
    ) -> list[AuthorizationDecision]:
        """Evaluates authorization for a batch of resource access requests.

        Used to filter search results and list endpoints by access rights.

        Args:
            contexts: List of individual resource authorization contexts.

        Returns:
            Ordered list of AuthorizationDecision, one per input context.
        """


class BaseResourceOwnershipChecker(ABC):
    """Abstract interface for evaluating resource ownership bypass rules.

    Certain resources grant additional permissions to the user who created them
    (e.g., document uploader can delete their own document regardless of role).
    """

    @abstractmethod
    def is_owner(
        self,
        caller_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Returns True if caller is the designated owner of the target resource.

        Args:
            caller_id: Authenticated user's UUID.
            resource_type: Type of the resource being evaluated.
            resource_id: UUID of the target resource.
            organization_id: Tenant boundary for the lookup.

        Returns:
            True if the caller owns the resource, False otherwise.
        """


class WorkspaceScopeLevel(str, Enum):
    """Hierarchical containment levels for multi-tenant workspace context."""

    ORGANIZATION = "organization"
    DEPARTMENT = "department"
    TEAM = "team"
    PROJECT = "project"


@dataclass
class WorkspaceScopeContext:
    """Represents an active multi-tier workspace scope for query routing and memory isolation."""

    organization_id: UUID
    department_id: UUID | None = None
    team_id: UUID | None = None
    project_id: UUID | None = None
    scope_level: WorkspaceScopeLevel = WorkspaceScopeLevel.ORGANIZATION


@dataclass
class AIWorkspaceSettings:
    """Workspace-level AI configurations and governance policies."""

    default_llm: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.2
    max_tokens_per_query: int = 2048
    citation_preferences: str = "in-text-brackets"
    token_quota_monthly: int = 10_000_000
    enable_department_isolation: bool = False


@dataclass
class AISecurityContext:
    """Security context establishing user identity and tenancy boundaries for AI requests."""

    organization_id: UUID
    user_id: UUID
    role: str = UserRole.EMPLOYEE.value
    email: str = ""
    permissions: set[str] = field(default_factory=set)
    is_authenticated: bool = True
    session_id: str | None = None
    ip_address: str | None = None
    department_id: UUID | None = None
    team_ids: set[UUID] = field(default_factory=set)
    project_ids: set[UUID] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.permissions:
            self.permissions = set(ROLE_PERMISSIONS.get(self.role, set()))

    def has_permission(self, permission: str | AIPermission) -> bool:
        """Verifies if the security context includes a required permission."""
        perm_value = permission.value if isinstance(permission, AIPermission) else str(permission)
        return perm_value in self.permissions

    def is_in_tenant(self, tenant_id: UUID) -> bool:
        """Ensures request target matches the authenticated organization tenancy barrier."""
        return self.organization_id == tenant_id

    def can_access_workspace(self, workspace_context: WorkspaceScopeContext) -> bool:
        """Verifies if the user is authorized to execute queries within the target workspace scope."""
        if not self.is_in_tenant(workspace_context.organization_id):
            return False

        # SuperAdmin and OrgAdmin possess organization-wide traversal authority
        if self.role in {UserRole.SUPER_ADMIN.value, UserRole.ORGANIZATION_ADMIN.value, "SuperAdmin", "OrgAdmin"}:
            return True

        # Organization-level scope is accessible to all active tenant members
        if workspace_context.scope_level == WorkspaceScopeLevel.ORGANIZATION:
            return True

        # Department scope check
        if workspace_context.scope_level == WorkspaceScopeLevel.DEPARTMENT:
            if workspace_context.department_id is None:
                return True
            return self.department_id == workspace_context.department_id

        # Team scope check
        if workspace_context.scope_level == WorkspaceScopeLevel.TEAM:
            if workspace_context.team_id is None:
                return True
            return workspace_context.team_id in self.team_ids

        # Project scope check
        if workspace_context.scope_level == WorkspaceScopeLevel.PROJECT:
            if workspace_context.project_id is None:
                return True
            return workspace_context.project_id in self.project_ids

        return False


@dataclass
class LLMMessage:
    """Represents a single message in an LLM conversation prompt."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class TokenUsage:
    """Token consumption and accounting container."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class LLMGenerationResult:
    """Result of an LLM generation call."""

    content: str
    model_name: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: str = "stop"
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIExecutionContext:
    """Multi-tenant execution context attached to all AI operations."""

    organization_id: UUID
    user_id: UUID
    session_id: str | None = None
    model_name: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int | None = 2048
    enable_cache: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    security_context: AISecurityContext | None = None

    def __post_init__(self) -> None:
        if self.security_context is None:
            self.security_context = AISecurityContext(
                organization_id=self.organization_id,
                user_id=self.user_id,
                session_id=self.session_id,
            )


@dataclass
class PromptTemplate:
    """Structured, parameterized prompt template."""

    name: str
    version: str
    template: str
    system_instruction: str = ""
    input_variables: list[str] = field(default_factory=list)
    default_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Schema defining a tool or function callable by the AI model."""

    name: str
    description: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Result returned by a tool execution dispatched by an AI agent."""

    tool_name: str
    call_id: str
    output: Any
    is_error: bool = False


class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the vector dimensionality of the embedding model (e.g. 1536 or 384)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the underlying model identifier string."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates vector embeddings for a list of document chunk strings.

        Args:
            texts: List of text chunks to embed.

        Returns:
            List of high-dimensional float vector embeddings.
        """

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generates a vector embedding for a single query string.

        Args:
            query: The user search query string.

        Returns:
            Single high-dimensional float vector embedding.
        """


class BaseLLMService(ABC):
    """Abstract interface for LLM orchestration (OpenAI, Anthropic, Local Ollama/vLLM)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model name identifier."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMGenerationResult:
        """Executes a single non-streaming generation call.

        Args:
            messages: List of structured conversation messages.
            temperature: Sampling temperature (0.0 for deterministic answers).
            max_tokens: Maximum tokens in completion.

        Returns:
            Structured LLMGenerationResult.
        """

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Executes a streaming generation call yielding tokens in real time.

        Args:
            messages: List of structured conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in completion.

        Yields:
            Token strings as they arrive from the LLM engine.
        """


class BasePromptService(ABC):
    """Abstract interface for loading and rendering versioned prompt templates."""

    @abstractmethod
    def render_prompt(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> list[LLMMessage]:
        """Renders messages from a named template and parameter map."""


class BaseSemanticCacheService(ABC):
    """Abstract interface for semantic query and response caching."""

    @abstractmethod
    async def get_cached_response(
        self,
        query: str,
        organization_id: UUID,
        similarity_threshold: float = 0.95,
    ) -> str | None:
        """Looks up a semantically equivalent query in cache."""

    @abstractmethod
    async def set_cached_response(
        self,
        query: str,
        response: str,
        organization_id: UUID,
        ttl_seconds: int = 86400,
    ) -> None:
        """Stores a query-response pair in semantic cache."""


class BaseTokenTrackerService(ABC):
    """Abstract interface for tracking token consumption and enterprise quotas."""

    @abstractmethod
    async def record_usage(
        self,
        context: AIExecutionContext,
        usage: TokenUsage,
    ) -> None:
        """Records token usage for billing, audit, and quota tracking."""

    @abstractmethod
    async def check_quota(self, organization_id: UUID) -> bool:
        """Verifies if tenant has remaining quota for AI inference."""


class BaseAssistantService(ABC):
    """Abstract interface for multi-tool AI assistant orchestration."""

    @abstractmethod
    async def process_user_intent(
        self,
        user_input: str,
        context: AIExecutionContext,
        available_tools: list[ToolDefinition] | None = None,
    ) -> LLMGenerationResult:
        """Processes intent, coordinates tool calling, and generates final answer."""


class BaseAIAccessController(ABC):
    """Abstract interface for policy enforcement, tool gating, and tenant boundary verification."""

    @abstractmethod
    def can_execute_query(self, query: str, context: AISecurityContext) -> bool:
        """Verifies if the security context is authorized to submit an AI prompt or query."""

    @abstractmethod
    def can_access_tool(self, tool_name: str, context: AISecurityContext) -> bool:
        """Verifies if the user's role and permissions permit executing the specified tool."""

    @abstractmethod
    def filter_tools_for_user(
        self,
        tools: list[ToolDefinition],
        context: AISecurityContext,
    ) -> list[ToolDefinition]:
        """Prunes tool definitions based on user RBAC permissions before LLM dispatch."""

    @abstractmethod
    def validate_tenant_boundary(
        self,
        target_org_id: UUID,
        context: AISecurityContext,
    ) -> bool:
        """Enforces hard isolation boundary ensuring target resource matches caller tenant."""


class BaseWorkspaceContextResolver(ABC):
    """Abstract interface for resolving hierarchical workspace contexts for active users."""

    @abstractmethod
    def resolve_context(
        self,
        user_id: UUID,
        organization_id: UUID,
        target_project_id: UUID | None = None,
    ) -> WorkspaceScopeContext:
        """Resolves active department, team, and project hierarchy for the user request."""


class BaseTenantIsolationValidator(ABC):
    """Abstract interface for strict multi-tenant validation and workspace boundary enforcement."""

    @abstractmethod
    def validate_tenant_access(
        self,
        context: AISecurityContext,
        target_org_id: UUID,
    ) -> bool:
        """Validates that caller's tenant boundary strictly matches target resource organization."""

    @abstractmethod
    def validate_scope_access(
        self,
        context: AISecurityContext,
        scope: WorkspaceScopeContext,
    ) -> bool:
        """Validates that caller possesses explicit access to target department/team/project scope."""



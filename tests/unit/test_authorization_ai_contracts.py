"""Unit Tests for Phase 1.6 User Role Management & Authorization Framework Contracts.

Verifies:
1. ResourceType enumeration values across all 10 target domains.
2. ResourceAuthorizationContext structure, defaults, and identity propagation.
3. AuthorizationDecision factory constructors (allow, deny) and payload serialization.
4. Action-based AIPermission definitions introduced in Phase 1.6.
5. Hierarchical role permission inheritance across Viewer, Employee/Member, ProjectManager,
   OrgAdmin, and SuperAdmin roles.
6. BaseAuthorizationPolicyEngine evaluation pipeline (tenant isolation, role permission,
   ownership override, and project scoping).
7. BaseResourceOwnershipChecker ownership bypass semantics for documents and meetings.
8. BaseAIAuthorizationFilter knowledge candidate pruning and knowledge graph entity gating.

Owner: Member 1 (Project Lead & AI Architect)
Sub-phase: Phase 1.6 User Role Management & Authorization Framework
Specification: devdocs/p1/p1.6.txt (Chapters 3–14, 18)
Architecture: docs/Architecture/authorization-architecture.md
"""

import unittest
from uuid import UUID, uuid4

from backend.app.services.ai import (
    EMPLOYEE_PERMISSIONS,
    ORG_ADMIN_PERMISSIONS,
    PROJECT_MANAGER_PERMISSIONS,
    ROLE_PERMISSIONS,
    SUPER_ADMIN_PERMISSIONS,
    VIEWER_PERMISSIONS,
    AIPermission,
    AuthorizationDecision,
    BaseAuthorizationPolicyEngine,
    BaseResourceOwnershipChecker,
    ResourceAuthorizationContext,
    ResourceType,
    UserRole,
)
from backend.app.services.rag import (
    BaseAIAuthorizationFilter,
    KGEntityRecord,
    RAGSecurityContext,
    RetrievalResult,
)


class MockResourceOwnershipChecker(BaseResourceOwnershipChecker):
    """Concrete test implementation of BaseResourceOwnershipChecker."""

    def __init__(self) -> None:
        # Maps (resource_type, resource_id) -> owner_user_id
        self.ownership_registry: dict[tuple[ResourceType, UUID], UUID] = {}

    def register_owner(
        self,
        resource_type: ResourceType,
        resource_id: UUID,
        owner_id: UUID,
    ) -> None:
        self.ownership_registry[(resource_type, resource_id)] = owner_id

    def is_owner(
        self,
        caller_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        organization_id: UUID,
    ) -> bool:
        owner = self.ownership_registry.get((resource_type, resource_id))
        return owner == caller_id if owner is not None else False


class MockAuthorizationPolicyEngine(BaseAuthorizationPolicyEngine):
    """Concrete test implementation of BaseAuthorizationPolicyEngine.

    Implements the 7-step pipeline from docs/Architecture/authorization-architecture.md:
    1. Tenant isolation check (caller_org_id == resource_org_id).
    2. Role permission check (required_permission in ROLE_PERMISSIONS[caller_role]).
    3. Ownership override check (owner bypass for permitted resources).
    4. Project membership check (if project-scoped).
    """

    OWNERSHIP_OVERRIDE_PERMISSIONS = {
        "document.update",
        "document.delete",
        "meeting.manage",
        "chat_session.delete",
    }

    def __init__(self, ownership_checker: BaseResourceOwnershipChecker | None = None) -> None:
        self.ownership_checker = ownership_checker or MockResourceOwnershipChecker()

    def evaluate_access(
        self,
        context: ResourceAuthorizationContext,
    ) -> AuthorizationDecision:
        # Step 1: Tenant Boundary (Hard isolation)
        if context.caller_org_id != context.resource_org_id:
            return AuthorizationDecision.deny(
                error_code="AUTH_ORGANIZATION_MISMATCH",
                reason="Cross-tenant access is strictly prohibited",
                required_permission=context.required_permission,
                resource_type=context.resource_type.value,
            )

        caller_permissions = ROLE_PERMISSIONS.get(context.caller_role, set())

        # Step 2: Base Role Permission Check
        has_role_permission = context.required_permission in caller_permissions

        # Step 3: Ownership Override Check (if base role lacks permission)
        is_owner = False
        if context.resource_owner_id and context.caller_id == context.resource_owner_id:
            is_owner = True
        elif self.ownership_checker.is_owner(
            caller_id=context.caller_id,
            resource_type=context.resource_type,
            resource_id=context.resource_id,
            organization_id=context.caller_org_id,
        ):
            is_owner = True

        if not has_role_permission:
            if is_owner and context.required_permission in self.OWNERSHIP_OVERRIDE_PERMISSIONS:
                has_role_permission = True
            else:
                return AuthorizationDecision.deny(
                    error_code="AUTH_PERMISSION_DENIED",
                    reason=f"Caller lacks required permission '{context.required_permission}'",
                    required_permission=context.required_permission,
                    resource_type=context.resource_type.value,
                )

        # Step 4: Project Membership Check (for project-scoped resources)
        # OrgAdmin / SuperAdmin bypass project scoping
        if context.caller_role not in (UserRole.ORGANIZATION_ADMIN.value, UserRole.SUPER_ADMIN.value, "OrgAdmin", "SuperAdmin"):
            if context.resource_project_id is not None:
                if context.resource_project_id not in context.caller_project_ids:
                    return AuthorizationDecision.deny(
                        error_code="AUTH_RESOURCE_FORBIDDEN",
                        reason="Caller is not a member of the required project workspace",
                        required_permission=context.required_permission,
                        resource_type=context.resource_type.value,
                    )

        return AuthorizationDecision.allow(
            reason=f"Access granted for action '{context.required_permission}'"
        )

    def evaluate_bulk_access(
        self,
        contexts: list[ResourceAuthorizationContext],
    ) -> list[AuthorizationDecision]:
        return [self.evaluate_access(ctx) for ctx in contexts]


class MockAIAuthorizationFilter(BaseAIAuthorizationFilter):
    """Concrete test implementation of BaseAIAuthorizationFilter."""

    def filter_knowledge_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        filtered: list[RetrievalResult] = []
        for candidate in candidates:
            # Tenant boundary
            if candidate.organization_id != security_context.organization_id:
                continue

            # Document ID level gating (if defined)
            if security_context.allowed_document_ids is not None:
                if candidate.document_id not in security_context.allowed_document_ids:
                    continue

            # Project level gating
            if candidate.project_id is not None:
                if not security_context.can_access_project(candidate.project_id):
                    continue

            filtered.append(candidate)
        return filtered

    def authorize_kg_traversal(
        self,
        entities: list[KGEntityRecord],
        security_context: RAGSecurityContext,
    ) -> list[KGEntityRecord]:
        authorized: list[KGEntityRecord] = []
        for entity in entities:
            if entity.organization_id != security_context.organization_id:
                continue
            if entity.source_document_id is not None and security_context.allowed_document_ids is not None:
                if entity.source_document_id not in security_context.allowed_document_ids:
                    continue
            authorized.append(entity)
        return authorized


class TestAuthorizationAIContracts(unittest.TestCase):
    """Test suite for Phase 1.6 authorization domain contracts."""

    def setUp(self) -> None:
        self.org_id = uuid4()
        self.foreign_org_id = uuid4()
        self.user_id = uuid4()
        self.project_id = uuid4()
        self.foreign_project_id = uuid4()
        self.document_id = uuid4()

    def test_resource_type_enum(self) -> None:
        """Verifies ResourceType enum values matches the 10 target domains."""
        self.assertEqual(ResourceType.DOCUMENT.value, "document")
        self.assertEqual(ResourceType.PROJECT.value, "project")
        self.assertEqual(ResourceType.TEAM.value, "team")
        self.assertEqual(ResourceType.DEPARTMENT.value, "department")
        self.assertEqual(ResourceType.MEETING.value, "meeting")
        self.assertEqual(ResourceType.CHAT_SESSION.value, "chat_session")
        self.assertEqual(ResourceType.AI_QUERY.value, "ai_query")
        self.assertEqual(ResourceType.ORGANIZATION.value, "organization")
        self.assertEqual(ResourceType.MEMBER.value, "member")
        self.assertEqual(ResourceType.INVITATION.value, "invitation")

    def test_resource_authorization_context(self) -> None:
        """Verifies ResourceAuthorizationContext instantiates properly with defaults."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.EMPLOYEE.value,
            caller_org_id=self.org_id,
            caller_project_ids={self.project_id},
            resource_type=ResourceType.DOCUMENT,
            required_permission="document.read",
        )
        self.assertEqual(ctx.caller_id, self.user_id)
        self.assertEqual(ctx.caller_role, UserRole.EMPLOYEE.value)
        self.assertEqual(ctx.caller_org_id, self.org_id)
        self.assertIn(self.project_id, ctx.caller_project_ids)
        self.assertEqual(ctx.resource_type, ResourceType.DOCUMENT)
        self.assertEqual(ctx.required_permission, "document.read")
        self.assertIsInstance(ctx.resource_id, UUID)

    def test_authorization_decision_factories(self) -> None:
        """Verifies AuthorizationDecision allow and deny classmethods."""
        allow_decision = AuthorizationDecision.allow("Permitted by policy")
        self.assertTrue(allow_decision.allowed)
        self.assertEqual(allow_decision.reason, "Permitted by policy")
        self.assertIsNone(allow_decision.error_code)

        deny_decision = AuthorizationDecision.deny(
            error_code="AUTH_PERMISSION_DENIED",
            reason="Caller lacks permission",
            required_permission="document.delete",
            resource_type="document",
        )
        self.assertFalse(deny_decision.allowed)
        self.assertEqual(deny_decision.error_code, "AUTH_PERMISSION_DENIED")
        self.assertEqual(deny_decision.required_permission, "document.delete")
        self.assertEqual(deny_decision.resource_type, "document")

    def test_phase_1_6_permissions_enum_definitions(self) -> None:
        """Verifies action-based AIPermission enum values defined in Phase 1.6."""
        self.assertEqual(AIPermission.DOCUMENT_CREATE.value, "document.create")
        self.assertEqual(AIPermission.DOCUMENT_READ.value, "document.read")
        self.assertEqual(AIPermission.DOCUMENT_UPDATE.value, "document.update")
        self.assertEqual(AIPermission.DOCUMENT_DELETE.value, "document.delete")
        self.assertEqual(AIPermission.PROJECT_MANAGE.value, "project.manage")
        self.assertEqual(AIPermission.MEETING_CREATE.value, "meeting.create")
        self.assertEqual(AIPermission.MEETING_READ.value, "meeting.read")
        self.assertEqual(AIPermission.MEETING_MANAGE.value, "meeting.manage")
        self.assertEqual(AIPermission.AI_CHAT.value, "ai.chat")
        self.assertEqual(AIPermission.AI_SEARCH.value, "ai.search")
        self.assertEqual(AIPermission.AI_ADMIN.value, "ai.admin")
        self.assertEqual(AIPermission.AI_CONFIG.value, "ai.config")
        self.assertEqual(AIPermission.ORGANIZATION_MANAGE.value, "organization.manage")
        self.assertEqual(AIPermission.ORGANIZATION_SETTINGS.value, "organization.settings")
        self.assertEqual(AIPermission.USER_INVITE.value, "user.invite")
        self.assertEqual(AIPermission.USER_MANAGE.value, "user.manage")
        self.assertEqual(AIPermission.USER_VIEW.value, "user.view")
        self.assertEqual(AIPermission.ANALYTICS_VIEW.value, "analytics.view")
        self.assertEqual(AIPermission.ANALYTICS_EXPORT.value, "analytics.export")
        self.assertEqual(AIPermission.AUDIT_READ.value, "audit.read")

    def test_role_permissions_hierarchy_phase_1_6(self) -> None:
        """Verifies hierarchical permission inheritance for all 5 canonical roles."""
        # Viewer checks
        self.assertIn("document.read", VIEWER_PERMISSIONS)
        self.assertIn("meeting.read", VIEWER_PERMISSIONS)
        self.assertIn("ai.chat", VIEWER_PERMISSIONS)
        self.assertIn("ai.search", VIEWER_PERMISSIONS)
        self.assertNotIn("document.create", VIEWER_PERMISSIONS)
        self.assertNotIn("document.delete", VIEWER_PERMISSIONS)

        # Employee checks (inherits Viewer + create/update)
        self.assertTrue(VIEWER_PERMISSIONS.issubset(EMPLOYEE_PERMISSIONS))
        self.assertIn("document.create", EMPLOYEE_PERMISSIONS)
        self.assertIn("document.update", EMPLOYEE_PERMISSIONS)
        self.assertNotIn("document.delete", EMPLOYEE_PERMISSIONS)
        self.assertNotIn("project.manage", EMPLOYEE_PERMISSIONS)

        # Project Manager checks (inherits Employee + delete/manage/invite)
        self.assertTrue(EMPLOYEE_PERMISSIONS.issubset(PROJECT_MANAGER_PERMISSIONS))
        self.assertIn("document.delete", PROJECT_MANAGER_PERMISSIONS)
        self.assertIn("project.manage", PROJECT_MANAGER_PERMISSIONS)
        self.assertIn("meeting.create", PROJECT_MANAGER_PERMISSIONS)
        self.assertIn("meeting.manage", PROJECT_MANAGER_PERMISSIONS)
        self.assertIn("user.invite", PROJECT_MANAGER_PERMISSIONS)
        self.assertNotIn("organization.manage", PROJECT_MANAGER_PERMISSIONS)

        # Org Admin checks (inherits PM + org/user/ai admin)
        self.assertTrue(PROJECT_MANAGER_PERMISSIONS.issubset(ORG_ADMIN_PERMISSIONS))
        self.assertIn("organization.manage", ORG_ADMIN_PERMISSIONS)
        self.assertIn("organization.settings", ORG_ADMIN_PERMISSIONS)
        self.assertIn("user.manage", ORG_ADMIN_PERMISSIONS)
        self.assertIn("ai.admin", ORG_ADMIN_PERMISSIONS)
        self.assertIn("ai.config", ORG_ADMIN_PERMISSIONS)
        self.assertIn("audit.read", ORG_ADMIN_PERMISSIONS)
        self.assertNotIn("org:create", ORG_ADMIN_PERMISSIONS)

        # Super Admin checks (inherits OrgAdmin + system org create)
        self.assertTrue(ORG_ADMIN_PERMISSIONS.issubset(SUPER_ADMIN_PERMISSIONS))
        self.assertIn("org:create", SUPER_ADMIN_PERMISSIONS)

    def test_policy_engine_cross_tenant_isolation(self) -> None:
        """Verifies policy engine rejects cross-tenant requests with AUTH_ORGANIZATION_MISMATCH."""
        engine = MockAuthorizationPolicyEngine()
        context = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.ORGANIZATION_ADMIN.value,
            caller_org_id=self.org_id,
            resource_id=self.document_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.foreign_org_id,  # Different tenant
            required_permission="document.read",
        )
        decision = engine.evaluate_access(context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_ORGANIZATION_MISMATCH")

    def test_policy_engine_insufficient_role_permission(self) -> None:
        """Verifies policy engine rejects requests lacking the required permission."""
        engine = MockAuthorizationPolicyEngine()
        context = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.VIEWER.value,
            caller_org_id=self.org_id,
            resource_id=self.document_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="document.delete",  # Viewer cannot delete
        )
        decision = engine.evaluate_access(context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_PERMISSION_DENIED")

    def test_policy_engine_ownership_override(self) -> None:
        """Verifies resource owner can perform permitted override actions (e.g. Employee deleting own doc)."""
        ownership_checker = MockResourceOwnershipChecker()
        ownership_checker.register_owner(
            resource_type=ResourceType.DOCUMENT,
            resource_id=self.document_id,
            owner_id=self.user_id,
        )
        engine = MockAuthorizationPolicyEngine(ownership_checker=ownership_checker)

        # Employee has no role permission for document.delete, but owns the doc
        context = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.EMPLOYEE.value,
            caller_org_id=self.org_id,
            resource_id=self.document_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_owner_id=self.user_id,
            required_permission="document.delete",
        )
        decision = engine.evaluate_access(context)
        self.assertTrue(decision.allowed)

    def test_policy_engine_project_membership_scoping(self) -> None:
        """Verifies non-admin caller cannot access resource in non-member project."""
        engine = MockAuthorizationPolicyEngine()

        # Employee belongs to self.project_id, but resource belongs to self.foreign_project_id
        context = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.EMPLOYEE.value,
            caller_org_id=self.org_id,
            caller_project_ids={self.project_id},
            resource_id=self.document_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_project_id=self.foreign_project_id,
            required_permission="document.read",
        )
        decision = engine.evaluate_access(context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_RESOURCE_FORBIDDEN")

    def test_policy_engine_bulk_evaluation(self) -> None:
        """Verifies bulk evaluation correctly computes decisions for mixed list."""
        engine = MockAuthorizationPolicyEngine()
        contexts = [
            # Allowed
            ResourceAuthorizationContext(
                caller_id=self.user_id,
                caller_role=UserRole.VIEWER.value,
                caller_org_id=self.org_id,
                resource_org_id=self.org_id,
                resource_type=ResourceType.DOCUMENT,
                required_permission="document.read",
            ),
            # Denied (Cross tenant)
            ResourceAuthorizationContext(
                caller_id=self.user_id,
                caller_role=UserRole.VIEWER.value,
                caller_org_id=self.org_id,
                resource_org_id=self.foreign_org_id,
                resource_type=ResourceType.DOCUMENT,
                required_permission="document.read",
            ),
        ]
        decisions = engine.evaluate_bulk_access(contexts)
        self.assertEqual(len(decisions), 2)
        self.assertTrue(decisions[0].allowed)
        self.assertFalse(decisions[1].allowed)
        self.assertEqual(decisions[1].error_code, "AUTH_ORGANIZATION_MISMATCH")

    def test_ai_authorization_filter(self) -> None:
        """Verifies BaseAIAuthorizationFilter prunes cross-tenant and inaccessible project candidates."""
        ai_filter = MockAIAuthorizationFilter()
        security_context = RAGSecurityContext(
            user_id=self.user_id,
            organization_id=self.org_id,
            role="Member",
            accessible_project_ids={self.project_id},
        )

        cand_valid = RetrievalResult(
            chunk_id=uuid4(),
            document_id=self.document_id,
            content="Valid org and project chunk",
            score=0.95,
            organization_id=self.org_id,
            project_id=self.project_id,
        )
        cand_cross_tenant = RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Cross-tenant chunk",
            score=0.99,
            organization_id=self.foreign_org_id,
            project_id=self.project_id,
        )
        cand_unauth_project = RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Unassigned project chunk",
            score=0.90,
            organization_id=self.org_id,
            project_id=self.foreign_project_id,
        )

        filtered = ai_filter.filter_knowledge_candidates(
            candidates=[cand_valid, cand_cross_tenant, cand_unauth_project],
            security_context=security_context,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].content, "Valid org and project chunk")

    def test_ai_authorization_filter_kg_entities(self) -> None:
        """Verifies BaseAIAuthorizationFilter gates KG entities based on document permissions."""
        ai_filter = MockAIAuthorizationFilter()
        allowed_doc = uuid4()
        restricted_doc = uuid4()

        security_context = RAGSecurityContext(
            user_id=self.user_id,
            organization_id=self.org_id,
            role="Member",
            allowed_document_ids={allowed_doc},
        )

        entity_allowed = KGEntityRecord(
            id=uuid4(),
            organization_id=self.org_id,
            name="AllowedEntity",
            entity_type="Concept",
            source_document_id=allowed_doc,
        )
        entity_restricted = KGEntityRecord(
            id=uuid4(),
            organization_id=self.org_id,
            name="RestrictedEntity",
            entity_type="Concept",
            source_document_id=restricted_doc,
        )
        entity_cross_tenant = KGEntityRecord(
            id=uuid4(),
            organization_id=self.foreign_org_id,
            name="ForeignEntity",
            entity_type="Concept",
            source_document_id=allowed_doc,
        )

        authorized = ai_filter.authorize_kg_traversal(
            entities=[entity_allowed, entity_restricted, entity_cross_tenant],
            security_context=security_context,
        )
        self.assertEqual(len(authorized), 1)
        self.assertEqual(authorized[0].name, "AllowedEntity")


if __name__ == "__main__":
    unittest.main()

"""Unit Tests for Phase 1.6 User Role Management & Authorization Framework.

Verifies:
1. Custom authorization error codes and exceptions.
2. AuthenticatedUser dynamic permission mapping and role helpers.
3. Concrete ResourceOwnershipChecker registration and validation.
4. Concrete AuthorizationPolicyEngine 7-step evaluation pipeline:
   - Hard tenant boundary isolation short-circuit.
   - Granular action-based role permission checks.
   - Resource-level ownership override privilege escalation.
   - Project containment and workspace membership verification.
   - OrgAdmin/SuperAdmin project membership bypass.
   - Bulk access evaluation.
   - Policy rules ABAC extension hook.
5. Concrete AIAuthorizationFilter candidate pruning and KG traversal gating.
6. FastAPI authorization dependencies (require_permission, require_role, check_resource_access).
7. @authorize decorator semantics.

Owner: Member 2 (Backend Lead)
Sub-phase: Phase 1.6 User Role Management & Authorization Framework
Specification: devdocs/p1/p1.6.txt (Chapters 1-19)
Architecture: docs/Architecture/authorization-architecture.md
"""

import unittest
from uuid import uuid4

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import (
    authorize,
    check_resource_access,
    require_permission,
    require_role,
)
from backend.app.core.authorization import (
    AuthorizationPolicyEngine,
    ResourceOwnershipChecker,
)
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import (
    AuthorizationException,
    OrganizationMismatchException,
    PermissionDeniedException,
    PolicyFailedException,
    ResourceForbiddenException,
    RoleRequiredException,
)
from backend.app.services.ai import (
    ResourceAuthorizationContext,
    ResourceType,
)
from backend.app.services.ai.authorization import (
    AIAuthorizationFilter,
)
from backend.app.services.rag.interfaces import (
    KGEntityRecord,
    RAGSecurityContext,
    RetrievalResult,
)


class TestAuthorizationExceptions(unittest.TestCase):
    """Verifies Phase 1.6 authorization exceptions and ErrorCode mappings."""

    def test_permission_denied_exception(self) -> None:
        exc = PermissionDeniedException(
            message="Caller lacks permission",
            details={"required_permission": "document.delete"},
        )
        self.assertIsInstance(exc, AuthorizationException)
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, ErrorCode.AUTH_PERMISSION_DENIED)
        self.assertEqual(exc.details["required_permission"], "document.delete")

    def test_role_required_exception(self) -> None:
        exc = RoleRequiredException(
            message="Role not met",
            details={"required_roles": ["OrgAdmin"]},
        )
        self.assertIsInstance(exc, AuthorizationException)
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, ErrorCode.AUTH_ROLE_REQUIRED)

    def test_resource_forbidden_exception(self) -> None:
        exc = ResourceForbiddenException(
            message="Workspace not joined",
            details={"resource_type": "project"},
        )
        self.assertIsInstance(exc, AuthorizationException)
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, ErrorCode.AUTH_RESOURCE_FORBIDDEN)

    def test_organization_mismatch_exception(self) -> None:
        exc = OrganizationMismatchException(
            message="Cross-tenant forbidden",
            details={"resource_type": "document"},
        )
        self.assertIsInstance(exc, AuthorizationException)
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, ErrorCode.AUTH_ORGANIZATION_MISMATCH)

    def test_policy_failed_exception(self) -> None:
        exc = PolicyFailedException(
            message="Evaluation failed",
        )
        self.assertIsInstance(exc, AuthorizationException)
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, ErrorCode.AUTH_POLICY_FAILED)


class TestAuthenticatedUserPermissions(unittest.TestCase):
    """Verifies AuthenticatedUser role-to-permission mapping and helper properties."""

    def setUp(self) -> None:
        self.org_id = uuid4()
        self.user_id = uuid4()

    def test_viewer_permissions(self) -> None:
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="viewer@corp.com",
            role=UserRole.VIEWER,
            organization_id=self.org_id,
        )
        self.assertTrue(user.has_permission("document.read"))
        self.assertTrue(user.has_permission("ai.chat"))
        self.assertTrue(user.has_permission("analytics.view"))
        self.assertFalse(user.has_permission("document.create"))
        self.assertFalse(user.has_permission("organization.manage"))
        self.assertFalse(user.is_org_admin)
        self.assertFalse(user.is_manager)

    def test_member_permissions(self) -> None:
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="member@corp.com",
            role=UserRole.MEMBER,
            organization_id=self.org_id,
        )
        self.assertTrue(user.has_permission("document.read"))
        self.assertTrue(user.has_permission("document.create"))
        self.assertTrue(user.has_permission("document.update"))
        self.assertTrue(user.has_permission("project.create"))
        self.assertFalse(user.has_permission("document.delete"))
        self.assertFalse(user.has_permission("user.invite"))
        self.assertFalse(user.is_org_admin)

    def test_project_manager_permissions(self) -> None:
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="pm@corp.com",
            role=UserRole.PROJECT_MANAGER,
            organization_id=self.org_id,
        )
        self.assertTrue(user.has_permission("document.delete"))
        self.assertTrue(user.has_permission("user.invite"))
        self.assertTrue(user.has_permission("project.manage"))
        self.assertFalse(user.has_permission("organization.manage"))
        self.assertFalse(user.has_permission("ai.admin"))
        self.assertTrue(user.is_manager)
        self.assertFalse(user.is_org_admin)

    def test_org_admin_permissions(self) -> None:
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="admin@corp.com",
            role=UserRole.ORG_ADMIN,
            organization_id=self.org_id,
        )
        self.assertTrue(user.has_permission("organization.manage"))
        self.assertTrue(user.has_permission("user.manage"))
        self.assertTrue(user.has_permission("audit.read"))
        self.assertTrue(user.has_permission("ai.admin"))
        self.assertFalse(user.has_permission("organization.create"))
        self.assertTrue(user.is_org_admin)

    def test_super_admin_permissions(self) -> None:
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="superadmin@corp.com",
            role=UserRole.SUPER_ADMIN,
            organization_id=self.org_id,
        )
        self.assertTrue(user.has_permission("organization.create"))
        self.assertTrue(user.has_permission("audit.read"))
        self.assertTrue(user.is_super_admin)
        self.assertTrue(user.is_org_admin)


class TestResourceOwnershipChecker(unittest.TestCase):
    """Verifies concrete ResourceOwnershipChecker registration and lookups."""

    def setUp(self) -> None:
        self.checker = ResourceOwnershipChecker()
        self.owner_id = uuid4()
        self.other_id = uuid4()
        self.doc_id = uuid4()
        self.org_id = uuid4()

    def test_unregistered_resource_not_owned(self) -> None:
        self.assertFalse(
            self.checker.is_owner(
                caller_id=self.owner_id,
                resource_type=ResourceType.DOCUMENT,
                resource_id=self.doc_id,
                organization_id=self.org_id,
            )
        )

    def test_registered_resource_ownership(self) -> None:
        self.checker.register_owner(ResourceType.DOCUMENT, self.doc_id, self.owner_id)
        self.assertTrue(
            self.checker.is_owner(
                caller_id=self.owner_id,
                resource_type=ResourceType.DOCUMENT,
                resource_id=self.doc_id,
                organization_id=self.org_id,
            )
        )
        self.assertFalse(
            self.checker.is_owner(
                caller_id=self.other_id,
                resource_type=ResourceType.DOCUMENT,
                resource_id=self.doc_id,
                organization_id=self.org_id,
            )
        )

    def test_clear_registry(self) -> None:
        self.checker.register_owner(ResourceType.DOCUMENT, self.doc_id, self.owner_id)
        self.checker.clear_registry()
        self.assertFalse(
            self.checker.is_owner(
                caller_id=self.owner_id,
                resource_type=ResourceType.DOCUMENT,
                resource_id=self.doc_id,
                organization_id=self.org_id,
            )
        )


class TestAuthorizationPolicyEngine(unittest.TestCase):
    """Verifies concrete AuthorizationPolicyEngine 7-step evaluation pipeline."""

    def setUp(self) -> None:
        self.checker = ResourceOwnershipChecker()
        self.engine = AuthorizationPolicyEngine(ownership_checker=self.checker)
        self.org_id = uuid4()
        self.foreign_org_id = uuid4()
        self.user_id = uuid4()
        self.owner_id = uuid4()
        self.project_id = uuid4()
        self.foreign_project_id = uuid4()
        self.resource_id = uuid4()

    def test_cross_tenant_rejection(self) -> None:
        """Step 1: Cross-tenant access is immediately rejected with AUTH_ORGANIZATION_MISMATCH."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.SUPER_ADMIN.value,
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.foreign_org_id,
            required_permission="document.read",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_ORGANIZATION_MISMATCH")
        self.assertIn("Cross-tenant", decision.reason)

    def test_role_permission_granted(self) -> None:
        """Step 2: Base role holds permission -> ALLOW."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="document.read",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertTrue(decision.allowed)
        self.assertIn("Access granted", decision.reason)

    def test_role_permission_denied(self) -> None:
        """Step 2 & 3: Caller lacks permission and is not owner -> AUTH_PERMISSION_DENIED."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="document.delete",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_PERMISSION_DENIED")

    def test_ownership_override_via_context_owner_id(self) -> None:
        """Step 3: Caller lacks permission in base role but is owner of document -> ALLOW."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",  # Member lacks document.delete
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_owner_id=self.user_id,  # Caller is the uploader!
            required_permission="document.delete",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertTrue(decision.allowed)

    def test_ownership_override_via_registered_checker(self) -> None:
        """Step 3: Ownership verified via ownership checker registry -> ALLOW."""
        self.checker.register_owner(ResourceType.MEETING, self.resource_id, self.user_id)
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",  # Member lacks meeting.manage
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.MEETING,
            resource_org_id=self.org_id,
            required_permission="meeting.manage",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertTrue(decision.allowed)

    def test_ownership_override_denied_for_ineligible_permission(self) -> None:
        """Ownership does not grant administrative permissions (e.g. organization.manage)."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.ORGANIZATION,
            resource_org_id=self.org_id,
            resource_owner_id=self.user_id,
            required_permission="organization.manage",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_PERMISSION_DENIED")

    def test_project_containment_denied_for_non_member(self) -> None:
        """Step 4: Caller holds permission but is not in target project workspace -> AUTH_RESOURCE_FORBIDDEN."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            caller_project_ids={self.project_id},
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_project_id=self.foreign_project_id,  # Project caller is not in!
            required_permission="document.read",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "AUTH_RESOURCE_FORBIDDEN")
        self.assertIn("not a member", decision.reason)

    def test_project_containment_allowed_for_member(self) -> None:
        """Step 4: Caller holds permission and belongs to target project workspace -> ALLOW."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            caller_project_ids={self.project_id},
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_project_id=self.project_id,
            required_permission="document.read",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertTrue(decision.allowed)

    def test_org_admin_bypasses_project_containment(self) -> None:
        """Step 4: OrgAdmin accesses project-scoped resource without explicit project membership."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role=UserRole.ORG_ADMIN.value,
            caller_org_id=self.org_id,
            caller_project_ids=set(),  # Not in project
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            resource_project_id=self.project_id,
            required_permission="document.read",
        )
        decision = self.engine.evaluate_access(ctx)
        self.assertTrue(decision.allowed)

    def test_bulk_evaluation(self) -> None:
        """Bulk evaluation returns decisions matching input contexts."""
        ctx1 = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=uuid4(),
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="document.read",
        )
        ctx2 = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=uuid4(),
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="organization.manage",
        )
        decisions = self.engine.evaluate_bulk_access([ctx1, ctx2])
        self.assertEqual(len(decisions), 2)
        self.assertTrue(decisions[0].allowed)
        self.assertFalse(decisions[1].allowed)

    def test_policy_rules_abac_hook(self) -> None:
        """evaluate_policy_rules extension point returns base decision."""
        ctx = ResourceAuthorizationContext(
            caller_id=self.user_id,
            caller_role="Member",
            caller_org_id=self.org_id,
            resource_id=self.resource_id,
            resource_type=ResourceType.DOCUMENT,
            resource_org_id=self.org_id,
            required_permission="document.read",
        )
        decision = self.engine.evaluate_policy_rules(ctx, custom_rules=[])
        self.assertTrue(decision.allowed)


class TestAIAuthorizationFilter(unittest.TestCase):
    """Verifies concrete AIAuthorizationFilter for RAG and KG gating."""

    def setUp(self) -> None:
        self.filter = AIAuthorizationFilter()
        self.org_id = uuid4()
        self.foreign_org_id = uuid4()
        self.doc1 = uuid4()
        self.doc2 = uuid4()
        self.project_a = uuid4()
        self.project_b = uuid4()

        self.sec_ctx = RAGSecurityContext(
            user_id=uuid4(),
            organization_id=self.org_id,
            role="Member",
            allowed_document_ids={self.doc1},
            accessible_project_ids={self.project_a},
        )

    def test_filter_knowledge_candidates_tenancy_and_scoping(self) -> None:
        cand_ok = RetrievalResult(
            chunk_id=uuid4(),
            document_id=self.doc1,
            content="Authorized content",
            score=0.9,
            organization_id=self.org_id,
            project_id=self.project_a,
        )
        cand_wrong_tenant = RetrievalResult(
            chunk_id=uuid4(),
            document_id=self.doc1,
            content="Foreign tenant content",
            score=0.95,
            organization_id=self.foreign_org_id,
            project_id=self.project_a,
        )
        cand_unallowed_doc = RetrievalResult(
            chunk_id=uuid4(),
            document_id=self.doc2,
            content="Doc not in allowed set",
            score=0.88,
            organization_id=self.org_id,
            project_id=self.project_a,
        )
        cand_unallowed_project = RetrievalResult(
            chunk_id=uuid4(),
            document_id=self.doc1,
            content="Project B content",
            score=0.85,
            organization_id=self.org_id,
            project_id=self.project_b,
        )

        filtered = self.filter.filter_knowledge_candidates(
            candidates=[cand_ok, cand_wrong_tenant, cand_unallowed_doc, cand_unallowed_project],
            security_context=self.sec_ctx,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].content, "Authorized content")

    def test_authorize_kg_traversal_gating(self) -> None:
        entity_ok = KGEntityRecord(
            id=uuid4(),
            name="AlphaEntity",
            entity_type="CONCEPT",
            organization_id=self.org_id,
            source_document_id=self.doc1,
        )
        entity_wrong_tenant = KGEntityRecord(
            id=uuid4(),
            name="BetaEntity",
            entity_type="CONCEPT",
            organization_id=self.foreign_org_id,
            source_document_id=self.doc1,
        )
        entity_unallowed_doc = KGEntityRecord(
            id=uuid4(),
            name="GammaEntity",
            entity_type="CONCEPT",
            organization_id=self.org_id,
            source_document_id=self.doc2,
        )

        authorized = self.filter.authorize_kg_traversal(
            entities=[entity_ok, entity_wrong_tenant, entity_unallowed_doc],
            security_context=self.sec_ctx,
        )
        self.assertEqual(len(authorized), 1)
        self.assertEqual(authorized[0].name, "AlphaEntity")


class TestFastAPIAuthorizationDependencies(unittest.IsolatedAsyncioTestCase):
    """Verifies require_permission and require_role dependency callables."""

    async def test_require_permission_granted(self) -> None:
        user = AuthenticatedUser(
            user_id=uuid4(),
            email="admin@test.com",
            role=UserRole.ORG_ADMIN,
            organization_id=uuid4(),
        )
        checker = require_permission("organization.manage")
        result = await checker(current_user=user)
        self.assertEqual(result.id, user.id)

    async def test_require_permission_denied_raises_exception(self) -> None:
        user = AuthenticatedUser(
            user_id=uuid4(),
            email="viewer@test.com",
            role=UserRole.VIEWER,
            organization_id=uuid4(),
        )
        checker = require_permission("organization.manage")
        with self.assertRaises(PermissionDeniedException) as ctx:
            await checker(current_user=user)
        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_PERMISSION_DENIED)
        self.assertEqual(ctx.exception.details["required_permission"], "organization.manage")

    async def test_require_role_granted(self) -> None:
        user = AuthenticatedUser(
            user_id=uuid4(),
            email="pm@test.com",
            role=UserRole.PROJECT_MANAGER,
            organization_id=uuid4(),
        )
        checker = require_role(UserRole.PROJECT_MANAGER, UserRole.ORG_ADMIN)
        result = await checker(current_user=user)
        self.assertEqual(result.id, user.id)

    async def test_require_role_denied_raises_exception(self) -> None:
        user = AuthenticatedUser(
            user_id=uuid4(),
            email="member@test.com",
            role=UserRole.MEMBER,
            organization_id=uuid4(),
        )
        checker = require_role(UserRole.ORG_ADMIN)
        with self.assertRaises(RoleRequiredException) as ctx:
            await checker(current_user=user)
        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_ROLE_REQUIRED)

    def test_check_resource_access_helper_exceptions(self) -> None:
        org_a = uuid4()
        org_b = uuid4()
        user_id = uuid4()

        # Organization mismatch
        ctx_mismatch = ResourceAuthorizationContext(
            caller_id=user_id,
            caller_role="Member",
            caller_org_id=org_a,
            resource_id=uuid4(),
            resource_org_id=org_b,
            required_permission="document.read",
        )
        with self.assertRaises(OrganizationMismatchException):
            check_resource_access(ctx_mismatch)

        # Permission denied
        ctx_denied = ResourceAuthorizationContext(
            caller_id=user_id,
            caller_role="Member",
            caller_org_id=org_a,
            resource_id=uuid4(),
            resource_org_id=org_a,
            required_permission="organization.manage",
        )
        with self.assertRaises(PermissionDeniedException):
            check_resource_access(ctx_denied)

    async def test_authorize_decorator(self) -> None:
        user_admin = AuthenticatedUser(
            user_id=uuid4(),
            email="admin@test.com",
            role=UserRole.ORG_ADMIN,
            organization_id=uuid4(),
        )
        user_viewer = AuthenticatedUser(
            user_id=uuid4(),
            email="viewer@test.com",
            role=UserRole.VIEWER,
            organization_id=uuid4(),
        )

        @authorize("organization.manage")
        async def protected_fn(current_user: AuthenticatedUser) -> str:
            return "SUCCESS"

        res = await protected_fn(current_user=user_admin)
        self.assertEqual(res, "SUCCESS")

        with self.assertRaises(PermissionDeniedException):
            await protected_fn(current_user=user_viewer)


if __name__ == "__main__":
    unittest.main()

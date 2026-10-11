"""Unit Tests for Organization Hierarchy, Multi-Tenancy & AI Workspace Contracts.

Verifies:
1. WorkspaceScopeLevel and WorkspaceScopeContext hierarchy levels.
2. AIWorkspaceSettings configuration models and defaults.
3. Expanded AIPermission enum for Phase 1.5 governance.
4. Hierarchical role permission inheritance across all 5 roles.
5. AISecurityContext workspace scope traversal and access rules.
6. BaseWorkspaceContextResolver and BaseTenantIsolationValidator interfaces.
7. RAGSecurityContext department and project access verification.
8. WorkspaceMemoryScope enumeration and BaseWorkspaceMemoryRouter routing & candidate pruning.
9. RetrievalResult hierarchical metadata mapping.

Owner: Member 1 (Project Lead & AI Architect)
Sub-phase: Phase 1.5 Organization, Team & Workspace Management
"""

import unittest
from uuid import UUID, uuid4

from backend.app.services.ai import (
    EMPLOYEE_PERMISSIONS,
    ORG_ADMIN_PERMISSIONS,
    PROJECT_MANAGER_PERMISSIONS,
    SUPER_ADMIN_PERMISSIONS,
    VIEWER_PERMISSIONS,
    AIPermission,
    AISecurityContext,
    AIWorkspaceSettings,
    BaseTenantIsolationValidator,
    BaseWorkspaceContextResolver,
    UserRole,
    WorkspaceScopeContext,
    WorkspaceScopeLevel,
)
from backend.app.services.rag import (
    BaseWorkspaceMemoryRouter,
    RAGSecurityContext,
    RetrievalResult,
    WorkspaceMemoryScope,
)


class MockWorkspaceContextResolver(BaseWorkspaceContextResolver):
    """Concrete mock implementation of BaseWorkspaceContextResolver for test validation."""

    def __init__(self) -> None:
        self.project_to_team: dict[UUID, UUID] = {}
        self.team_to_dept: dict[UUID, UUID] = {}

    def resolve_context(
        self,
        user_id: UUID,
        organization_id: UUID,
        target_project_id: UUID | None = None,
    ) -> WorkspaceScopeContext:
        if target_project_id is not None:
            team_id = self.project_to_team.get(target_project_id)
            dept_id = self.team_to_dept.get(team_id) if team_id else None
            return WorkspaceScopeContext(
                organization_id=organization_id,
                department_id=dept_id,
                team_id=team_id,
                project_id=target_project_id,
                scope_level=WorkspaceScopeLevel.PROJECT,
            )
        return WorkspaceScopeContext(
            organization_id=organization_id,
            scope_level=WorkspaceScopeLevel.ORGANIZATION,
        )


class MockTenantIsolationValidator(BaseTenantIsolationValidator):
    """Concrete mock implementation of BaseTenantIsolationValidator for test validation."""

    def validate_tenant_access(
        self,
        context: AISecurityContext,
        target_org_id: UUID,
    ) -> bool:
        if not context.is_authenticated:
            return False
        return context.is_in_tenant(target_org_id)

    def validate_scope_access(
        self,
        context: AISecurityContext,
        scope: WorkspaceScopeContext,
    ) -> bool:
        if not self.validate_tenant_access(context, scope.organization_id):
            return False
        return context.can_access_workspace(scope)


class MockWorkspaceMemoryRouter(BaseWorkspaceMemoryRouter):
    """Concrete mock implementation of BaseWorkspaceMemoryRouter for test validation."""

    def route_query_scopes(
        self,
        query: str,
        security_context: RAGSecurityContext,
        requested_scope: WorkspaceMemoryScope | None = None,
    ) -> list[WorkspaceMemoryScope]:
        if requested_scope is not None:
            return [requested_scope]
        # Default hierarchical routing order: Local project -> Team -> Department -> Org
        return [
            WorkspaceMemoryScope.PROJECT_LOCAL,
            WorkspaceMemoryScope.TEAM_WIDE,
            WorkspaceMemoryScope.DEPARTMENT_WIDE,
            WorkspaceMemoryScope.ORG_WIDE,
        ]

    def filter_candidates_by_workspace(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        filtered: list[RetrievalResult] = []
        for c in candidates:
            # Check document-level gating
            if not security_context.can_access_document(c.document_id):
                continue
            # Check project-level gating
            if c.project_id is not None and not security_context.can_access_project(c.project_id):
                continue
            # Check department-level gating
            if c.department_id is not None and not security_context.can_access_department(c.department_id):
                continue
            filtered.append(c)
        return filtered


class TestWorkspaceAIContracts(unittest.TestCase):
    """Test suite verifying Phase 1.5 Organization, Workspace & AI Hierarchy Contracts."""

    def setUp(self) -> None:
        self.org_a = uuid4()
        self.org_b = uuid4()
        self.dept_eng = uuid4()
        self.dept_sales = uuid4()
        self.team_backend = uuid4()
        self.team_frontend = uuid4()
        self.project_1 = uuid4()
        self.project_2 = uuid4()
        self.project_confidential = uuid4()

        self.user_admin = uuid4()
        self.user_pm = uuid4()
        self.user_emp = uuid4()
        self.user_viewer = uuid4()

    def test_workspace_scope_levels_and_context(self) -> None:
        """Verifies WorkspaceScopeLevel and WorkspaceScopeContext attributes."""
        self.assertEqual(WorkspaceScopeLevel.ORGANIZATION.value, "organization")
        self.assertEqual(WorkspaceScopeLevel.DEPARTMENT.value, "department")
        self.assertEqual(WorkspaceScopeLevel.TEAM.value, "team")
        self.assertEqual(WorkspaceScopeLevel.PROJECT.value, "project")

        ctx = WorkspaceScopeContext(
            organization_id=self.org_a,
            department_id=self.dept_eng,
            team_id=self.team_backend,
            project_id=self.project_1,
            scope_level=WorkspaceScopeLevel.PROJECT,
        )
        self.assertEqual(ctx.organization_id, self.org_a)
        self.assertEqual(ctx.department_id, self.dept_eng)
        self.assertEqual(ctx.team_id, self.team_backend)
        self.assertEqual(ctx.project_id, self.project_1)
        self.assertEqual(ctx.scope_level, WorkspaceScopeLevel.PROJECT)

    def test_ai_workspace_settings_defaults_and_override(self) -> None:
        """Verifies AIWorkspaceSettings default configurations and custom values."""
        settings = AIWorkspaceSettings()
        self.assertEqual(settings.default_llm, "gpt-4o")
        self.assertEqual(settings.embedding_model, "text-embedding-3-small")
        self.assertEqual(settings.temperature, 0.2)
        self.assertEqual(settings.max_tokens_per_query, 2048)
        self.assertEqual(settings.citation_preferences, "in-text-brackets")
        self.assertEqual(settings.token_quota_monthly, 10_000_000)
        self.assertFalse(settings.enable_department_isolation)

        custom = AIWorkspaceSettings(
            default_llm="claude-3-5-sonnet",
            enable_department_isolation=True,
            token_quota_monthly=25_000_000,
        )
        self.assertEqual(custom.default_llm, "claude-3-5-sonnet")
        self.assertTrue(custom.enable_department_isolation)
        self.assertEqual(custom.token_quota_monthly, 25_000_000)

    def test_phase_1_5_permissions_defined(self) -> None:
        """Verifies Phase 1.5 granular organizational governance permissions exist."""
        self.assertEqual(AIPermission.ORG_CREATE.value, "org:create")
        self.assertEqual(AIPermission.ORG_READ.value, "org:read")
        self.assertEqual(AIPermission.ORG_UPDATE.value, "org:update")
        self.assertEqual(AIPermission.ORG_DELETE.value, "org:delete")
        self.assertEqual(AIPermission.ORG_SETTINGS.value, "org:settings")

        self.assertEqual(AIPermission.DEPT_CREATE.value, "dept:create")
        self.assertEqual(AIPermission.DEPT_READ.value, "dept:read")
        self.assertEqual(AIPermission.DEPT_UPDATE.value, "dept:update")
        self.assertEqual(AIPermission.DEPT_DELETE.value, "dept:delete")

        self.assertEqual(AIPermission.TEAM_CREATE.value, "team:create")
        self.assertEqual(AIPermission.TEAM_READ.value, "team:read")
        self.assertEqual(AIPermission.TEAM_UPDATE.value, "team:update")
        self.assertEqual(AIPermission.TEAM_DELETE.value, "team:delete")

        self.assertEqual(AIPermission.PROJECT_CREATE.value, "project:create")
        self.assertEqual(AIPermission.PROJECT_READ.value, "project:read")
        self.assertEqual(AIPermission.PROJECT_UPDATE.value, "project:update")
        self.assertEqual(AIPermission.PROJECT_DELETE.value, "project:delete")
        self.assertEqual(AIPermission.PROJECT_MEMBERSHIP.value, "project:membership")

        self.assertEqual(AIPermission.INVITATION_CREATE.value, "invitation:create")
        self.assertEqual(AIPermission.INVITATION_READ.value, "invitation:read")
        self.assertEqual(AIPermission.INVITATION_REVOKE.value, "invitation:revoke")

        self.assertEqual(AIPermission.MEMBER_READ.value, "member:read")
        self.assertEqual(AIPermission.MEMBER_UPDATE.value, "member:update")
        self.assertEqual(AIPermission.MEMBER_REMOVE.value, "member:remove")

    def test_role_permissions_hierarchy_phase_1_5(self) -> None:
        """Verifies strict hierarchical permission inheritance for workspace operations."""
        # Viewer has read-only perms for org, dept, team, project, members
        self.assertIn(AIPermission.ORG_READ.value, VIEWER_PERMISSIONS)
        self.assertIn(AIPermission.DEPT_READ.value, VIEWER_PERMISSIONS)
        self.assertIn(AIPermission.TEAM_READ.value, VIEWER_PERMISSIONS)
        self.assertIn(AIPermission.PROJECT_READ.value, VIEWER_PERMISSIONS)
        self.assertIn(AIPermission.MEMBER_READ.value, VIEWER_PERMISSIONS)
        self.assertNotIn(AIPermission.PROJECT_CREATE.value, VIEWER_PERMISSIONS)

        # Employee inherits Viewer and can create/update projects & read invites
        self.assertTrue(VIEWER_PERMISSIONS.issubset(EMPLOYEE_PERMISSIONS))
        self.assertIn(AIPermission.PROJECT_CREATE.value, EMPLOYEE_PERMISSIONS)
        self.assertIn(AIPermission.PROJECT_UPDATE.value, EMPLOYEE_PERMISSIONS)
        self.assertIn(AIPermission.INVITATION_READ.value, EMPLOYEE_PERMISSIONS)
        self.assertNotIn(AIPermission.TEAM_CREATE.value, EMPLOYEE_PERMISSIONS)

        # Project Manager inherits Employee and can create teams, delete projects & invite
        self.assertTrue(EMPLOYEE_PERMISSIONS.issubset(PROJECT_MANAGER_PERMISSIONS))
        self.assertIn(AIPermission.TEAM_CREATE.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertIn(AIPermission.TEAM_UPDATE.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertIn(AIPermission.PROJECT_DELETE.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertIn(AIPermission.PROJECT_MEMBERSHIP.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertIn(AIPermission.INVITATION_CREATE.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertNotIn(AIPermission.ORG_SETTINGS.value, PROJECT_MANAGER_PERMISSIONS)

        # Org Admin inherits PM and can manage settings, depts, teams, invites & members
        self.assertTrue(PROJECT_MANAGER_PERMISSIONS.issubset(ORG_ADMIN_PERMISSIONS))
        self.assertIn(AIPermission.ORG_SETTINGS.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.ORG_UPDATE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.ORG_DELETE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.DEPT_CREATE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.DEPT_DELETE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.TEAM_DELETE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.INVITATION_REVOKE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.MEMBER_UPDATE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.MEMBER_REMOVE.value, ORG_ADMIN_PERMISSIONS)
        self.assertNotIn(AIPermission.ORG_CREATE.value, ORG_ADMIN_PERMISSIONS)

        # Super Admin has ORG_CREATE
        self.assertTrue(ORG_ADMIN_PERMISSIONS.issubset(SUPER_ADMIN_PERMISSIONS))
        self.assertIn(AIPermission.ORG_CREATE.value, SUPER_ADMIN_PERMISSIONS)

    def test_ai_security_context_workspace_traversal(self) -> None:
        """Verifies AISecurityContext.can_access_workspace() enforces hierarchy bounds."""
        # Employee belonging to dept_eng, team_backend, project_1
        emp_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_emp,
            role=UserRole.EMPLOYEE.value,
            department_id=self.dept_eng,
            team_ids={self.team_backend},
            project_ids={self.project_1},
        )

        # 1. Cross-tenant check
        cross_scope = WorkspaceScopeContext(organization_id=self.org_b)
        self.assertFalse(emp_ctx.can_access_workspace(cross_scope))

        # 2. Org-wide scope within tenant
        org_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            scope_level=WorkspaceScopeLevel.ORGANIZATION,
        )
        self.assertTrue(emp_ctx.can_access_workspace(org_scope))

        # 3. Department scope
        eng_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            department_id=self.dept_eng,
            scope_level=WorkspaceScopeLevel.DEPARTMENT,
        )
        sales_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            department_id=self.dept_sales,
            scope_level=WorkspaceScopeLevel.DEPARTMENT,
        )
        self.assertTrue(emp_ctx.can_access_workspace(eng_scope))
        self.assertFalse(emp_ctx.can_access_workspace(sales_scope))

        # 4. Team scope
        backend_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            team_id=self.team_backend,
            scope_level=WorkspaceScopeLevel.TEAM,
        )
        frontend_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            team_id=self.team_frontend,
            scope_level=WorkspaceScopeLevel.TEAM,
        )
        self.assertTrue(emp_ctx.can_access_workspace(backend_scope))
        self.assertFalse(emp_ctx.can_access_workspace(frontend_scope))

        # 5. Project scope
        proj1_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            project_id=self.project_1,
            scope_level=WorkspaceScopeLevel.PROJECT,
        )
        proj2_scope = WorkspaceScopeContext(
            organization_id=self.org_a,
            project_id=self.project_2,
            scope_level=WorkspaceScopeLevel.PROJECT,
        )
        self.assertTrue(emp_ctx.can_access_workspace(proj1_scope))
        self.assertFalse(emp_ctx.can_access_workspace(proj2_scope))

        # 6. OrgAdmin has universal traversal across all scopes in tenant
        admin_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_admin,
            role=UserRole.ORGANIZATION_ADMIN.value,
        )
        self.assertTrue(admin_ctx.can_access_workspace(eng_scope))
        self.assertTrue(admin_ctx.can_access_workspace(sales_scope))
        self.assertTrue(admin_ctx.can_access_workspace(frontend_scope))
        self.assertTrue(admin_ctx.can_access_workspace(proj2_scope))
        self.assertFalse(admin_ctx.can_access_workspace(cross_scope))

    def test_mock_workspace_context_resolver_and_tenant_validator(self) -> None:
        """Verifies BaseWorkspaceContextResolver and BaseTenantIsolationValidator implementations."""
        resolver = MockWorkspaceContextResolver()
        resolver.project_to_team[self.project_1] = self.team_backend
        resolver.team_to_dept[self.team_backend] = self.dept_eng

        validator = MockTenantIsolationValidator()

        # Resolve context for project
        resolved = resolver.resolve_context(self.user_emp, self.org_a, self.project_1)
        self.assertEqual(resolved.organization_id, self.org_a)
        self.assertEqual(resolved.department_id, self.dept_eng)
        self.assertEqual(resolved.team_id, self.team_backend)
        self.assertEqual(resolved.project_id, self.project_1)
        self.assertEqual(resolved.scope_level, WorkspaceScopeLevel.PROJECT)

        # Validate access
        emp_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_emp,
            department_id=self.dept_eng,
            team_ids={self.team_backend},
            project_ids={self.project_1},
        )
        self.assertTrue(validator.validate_tenant_access(emp_ctx, self.org_a))
        self.assertFalse(validator.validate_tenant_access(emp_ctx, self.org_b))
        self.assertTrue(validator.validate_scope_access(emp_ctx, resolved))

    def test_rag_security_context_hierarchy_gating(self) -> None:
        """Verifies RAGSecurityContext department and project access controls."""
        rag_ctx = RAGSecurityContext(
            user_id=self.user_emp,
            organization_id=self.org_a,
            department_id=self.dept_eng,
            team_ids={self.team_backend},
            accessible_project_ids={self.project_1},
        )

        self.assertTrue(rag_ctx.is_in_tenant(self.org_a))
        self.assertFalse(rag_ctx.is_in_tenant(self.org_b))

        self.assertTrue(rag_ctx.can_access_project(self.project_1))
        self.assertFalse(rag_ctx.can_access_project(self.project_2))

        self.assertTrue(rag_ctx.can_access_department(self.dept_eng))
        self.assertFalse(rag_ctx.can_access_department(self.dept_sales))

        # Admin with unrestricted projects (accessible_project_ids is None)
        admin_rag_ctx = RAGSecurityContext(
            user_id=self.user_admin,
            organization_id=self.org_a,
            accessible_project_ids=None,
            department_id=None,
        )
        self.assertTrue(admin_rag_ctx.can_access_project(self.project_1))
        self.assertTrue(admin_rag_ctx.can_access_project(self.project_confidential))
        self.assertTrue(admin_rag_ctx.can_access_department(self.dept_sales))

    def test_mock_workspace_memory_router(self) -> None:
        """Verifies BaseWorkspaceMemoryRouter routes scopes and prunes unauthorized candidates."""
        router = MockWorkspaceMemoryRouter()

        rag_ctx = RAGSecurityContext(
            user_id=self.user_emp,
            organization_id=self.org_a,
            department_id=self.dept_eng,
            accessible_project_ids={self.project_1},
            allowed_document_ids=None,
        )

        # Routing verification
        default_scopes = router.route_query_scopes("any query", rag_ctx)
        self.assertEqual(len(default_scopes), 4)
        self.assertEqual(default_scopes[0], WorkspaceMemoryScope.PROJECT_LOCAL)

        explicit_scopes = router.route_query_scopes(
            "team query",
            rag_ctx,
            requested_scope=WorkspaceMemoryScope.TEAM_WIDE,
        )
        self.assertEqual(explicit_scopes, [WorkspaceMemoryScope.TEAM_WIDE])

        # Candidate pruning verification
        c_proj1 = RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Project 1 specification",
            score=0.92,
            project_id=self.project_1,
            department_id=self.dept_eng,
        )
        c_proj2 = RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Project 2 design doc",
            score=0.88,
            project_id=self.project_2,
            department_id=self.dept_eng,
        )
        c_sales = RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Sales commission plan",
            score=0.85,
            department_id=self.dept_sales,
        )

        candidates = [c_proj1, c_proj2, c_sales]
        pruned = router.filter_candidates_by_workspace(candidates, rag_ctx)

        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0].content, "Project 1 specification")
        self.assertEqual(pruned[0].project_id, self.project_1)


if __name__ == "__main__":
    unittest.main()

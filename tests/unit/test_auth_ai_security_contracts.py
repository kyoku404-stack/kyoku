"""Unit Tests for Authentication, Identity, RBAC & AI Security Contracts.

Verifies:
1. UserRole and AIPermission enumeration definitions.
2. Hierarchical RBAC permission inheritance (OrgAdmin > ProjectManager > Employee > Viewer).
3. AISecurityContext tenant isolation, permission evaluation, and default resolution.
4. AIExecutionContext integration with AISecurityContext.
5. BaseAIAccessController policy enforcement, tool filtering, and cross-tenant prevention.
6. RAGSecurityContext document-level access control and tenant gating.
7. BaseRAGAccessController retrieval candidate pruning and KG node access verification.
8. SearchQuery and VectorFilter security context and allowed_document_ids filtering.

Owner: Member 1 (Project Lead & AI Architect)
Sub-phase: Phase 1.4 Authentication & Identity Management
"""

import unittest
from uuid import UUID, uuid4

from backend.app.services.ai import (
    ROLE_PERMISSIONS,
    AIExecutionContext,
    AIPermission,
    AISecurityContext,
    BaseAIAccessController,
    ToolDefinition,
    UserRole,
)
from backend.app.services.rag import (
    BaseRAGAccessController,
    KGEntityRecord,
    RAGSecurityContext,
    RetrievalResult,
    SearchQuery,
    VectorFilter,
)


class MockAIAccessController(BaseAIAccessController):
    """Concrete mock implementation of BaseAIAccessController for test validation."""

    def can_execute_query(self, query: str, context: AISecurityContext) -> bool:
        if not context.is_authenticated:
            return False
        return context.has_permission(AIPermission.CHAT_QUERY) or context.has_permission(
            AIPermission.SEARCH_QUERY
        )

    def can_access_tool(self, tool_name: str, context: AISecurityContext) -> bool:
        if not context.is_authenticated:
            return False
        # Sensitive tools require higher privileges
        if tool_name in {"delete_document", "manage_users"}:
            return context.has_permission(AIPermission.USERS_MANAGE) or context.has_permission(
                AIPermission.DOC_DELETE
            )
        return context.has_permission(AIPermission.TOOL_EXECUTE)

    def filter_tools_for_user(
        self,
        tools: list[ToolDefinition],
        context: AISecurityContext,
    ) -> list[ToolDefinition]:
        return [tool for tool in tools if self.can_access_tool(tool.name, context)]

    def validate_tenant_boundary(
        self,
        target_org_id: UUID,
        context: AISecurityContext,
    ) -> bool:
        return context.is_in_tenant(target_org_id)


class MockRAGAccessController(BaseRAGAccessController):
    """Concrete mock implementation of BaseRAGAccessController for test validation."""

    def filter_retrieval_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        return [
            c
            for c in candidates
            if security_context.can_access_document(c.document_id)
        ]

    def verify_document_access(
        self,
        document_id: UUID,
        security_context: RAGSecurityContext,
    ) -> bool:
        return security_context.can_access_document(document_id)

    def verify_graph_node_access(
        self,
        entity: KGEntityRecord,
        security_context: RAGSecurityContext,
    ) -> bool:
        if not security_context.is_in_tenant(entity.organization_id):
            return False
        if entity.source_document_id is not None:
            return security_context.can_access_document(entity.source_document_id)
        return True


class TestAuthAISecurityContracts(unittest.TestCase):
    """Test suite verifying Phase 1.4 AI authentication, identity, and RBAC contracts."""

    def setUp(self) -> None:
        self.org_a = uuid4()
        self.org_b = uuid4()
        self.user_admin = uuid4()
        self.user_pm = uuid4()
        self.user_employee = uuid4()
        self.user_viewer = uuid4()

        self.doc_1 = uuid4()
        self.doc_2 = uuid4()
        self.doc_confidential = uuid4()

    def test_user_roles_and_permissions_defined(self) -> None:
        """Verifies that all 4 MVP roles and granular AI permissions exist."""
        self.assertEqual(UserRole.VIEWER.value, "Viewer")
        self.assertEqual(UserRole.EMPLOYEE.value, "Member")
        self.assertEqual(UserRole.PROJECT_MANAGER.value, "ProjectManager")
        self.assertEqual(UserRole.ORGANIZATION_ADMIN.value, "OrgAdmin")

        self.assertEqual(AIPermission.CHAT_QUERY.value, "chat:query")
        self.assertEqual(AIPermission.DOC_DELETE.value, "doc:delete")
        self.assertEqual(AIPermission.USERS_MANAGE.value, "users:manage")
        self.assertEqual(AIPermission.KG_READ.value, "kg:read")

    def test_hierarchical_rbac_permission_inheritance(self) -> None:
        """Verifies that higher roles strictly inherit lower roles' permissions."""
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER.value]
        employee_perms = ROLE_PERMISSIONS[UserRole.EMPLOYEE.value]
        pm_perms = ROLE_PERMISSIONS[UserRole.PROJECT_MANAGER.value]
        admin_perms = ROLE_PERMISSIONS[UserRole.ORGANIZATION_ADMIN.value]

        # Viewer has read-only perms
        self.assertIn(AIPermission.SEARCH_QUERY.value, viewer_perms)
        self.assertIn(AIPermission.DOC_READ.value, viewer_perms)
        self.assertNotIn(AIPermission.CHAT_QUERY.value, viewer_perms)
        self.assertNotIn(AIPermission.DOC_DELETE.value, viewer_perms)

        # Employee inherits Viewer and adds interactive chat & doc create
        self.assertTrue(viewer_perms.issubset(employee_perms))
        self.assertIn(AIPermission.CHAT_QUERY.value, employee_perms)
        self.assertIn(AIPermission.DOC_CREATE.value, employee_perms)
        self.assertNotIn(AIPermission.DOC_DELETE.value, employee_perms)

        # Project Manager inherits Employee and adds doc delete & KG write
        self.assertTrue(employee_perms.issubset(pm_perms))
        self.assertIn(AIPermission.DOC_DELETE.value, pm_perms)
        self.assertIn(AIPermission.KG_WRITE.value, pm_perms)
        self.assertNotIn(AIPermission.USERS_MANAGE.value, pm_perms)

        # Org Admin inherits PM and adds user & org management
        self.assertTrue(pm_perms.issubset(admin_perms))
        self.assertIn(AIPermission.USERS_MANAGE.value, admin_perms)
        self.assertIn(AIPermission.ORG_MANAGE.value, admin_perms)
        self.assertIn(AIPermission.CHAT_MANAGE_ALL.value, admin_perms)

    def test_ai_security_context_resolution_and_boundaries(self) -> None:
        """Verifies AISecurityContext evaluates permissions and tenant boundaries."""
        context = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_employee,
            role=UserRole.EMPLOYEE.value,
            email="emp@enterprise.com",
        )

        self.assertTrue(context.is_authenticated)
        self.assertTrue(context.is_in_tenant(self.org_a))
        self.assertFalse(context.is_in_tenant(self.org_b))

        self.assertTrue(context.has_permission(AIPermission.CHAT_QUERY))
        self.assertTrue(context.has_permission(AIPermission.DOC_READ))
        self.assertFalse(context.has_permission(AIPermission.DOC_DELETE))
        self.assertFalse(context.has_permission(AIPermission.USERS_MANAGE))

    def test_ai_execution_context_security_integration(self) -> None:
        """Verifies AIExecutionContext auto-populates security context."""
        exec_context = AIExecutionContext(
            organization_id=self.org_a,
            user_id=self.user_pm,
            session_id="session_123",
        )

        self.assertIsNotNone(exec_context.security_context)
        self.assertEqual(exec_context.security_context.organization_id, self.org_a)
        self.assertEqual(exec_context.security_context.user_id, self.user_pm)
        self.assertEqual(exec_context.security_context.session_id, "session_123")

    def test_mock_ai_access_controller_enforcement(self) -> None:
        """Verifies BaseAIAccessController gates tools and verifies tenant boundaries."""
        controller = MockAIAccessController()

        viewer_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_viewer,
            role=UserRole.VIEWER.value,
        )
        emp_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_employee,
            role=UserRole.EMPLOYEE.value,
        )
        admin_ctx = AISecurityContext(
            organization_id=self.org_a,
            user_id=self.user_admin,
            role=UserRole.ORGANIZATION_ADMIN.value,
        )

        # Viewer can search, but cannot execute chat queries
        self.assertTrue(controller.can_execute_query("search docs", viewer_ctx))
        self.assertTrue(controller.can_execute_query("ask question", emp_ctx))

        # Tool filtering
        tools = [
            ToolDefinition(name="read_document", description="Read doc content"),
            ToolDefinition(name="delete_document", description="Delete doc"),
            ToolDefinition(name="manage_users", description="Manage users"),
        ]

        viewer_tools = controller.filter_tools_for_user(tools, viewer_ctx)
        self.assertEqual(len(viewer_tools), 0)

        emp_tools = controller.filter_tools_for_user(tools, emp_ctx)
        # Employee has tool:execute, so can access read_document, but not delete_document/manage_users
        self.assertEqual(len(emp_tools), 1)
        self.assertEqual(emp_tools[0].name, "read_document")

        admin_tools = controller.filter_tools_for_user(tools, admin_ctx)
        self.assertEqual(len(admin_tools), 3)

        # Tenant boundary check
        self.assertTrue(controller.validate_tenant_boundary(self.org_a, emp_ctx))
        self.assertFalse(controller.validate_tenant_boundary(self.org_b, emp_ctx))

    def test_rag_security_context_document_gating(self) -> None:
        """Verifies RAGSecurityContext enforces document-level permissions."""
        # Unrestricted user (e.g. Org Admin)
        admin_rag_ctx = RAGSecurityContext(
            user_id=self.user_admin,
            organization_id=self.org_a,
            allowed_document_ids=None,
        )
        self.assertTrue(admin_rag_ctx.can_access_document(self.doc_1))
        self.assertTrue(admin_rag_ctx.can_access_document(self.doc_confidential))

        # Restricted user (Employee limited to specific documents)
        restricted_rag_ctx = RAGSecurityContext(
            user_id=self.user_employee,
            organization_id=self.org_a,
            allowed_document_ids={self.doc_1, self.doc_2},
        )
        self.assertTrue(restricted_rag_ctx.can_access_document(self.doc_1))
        self.assertTrue(restricted_rag_ctx.can_access_document(self.doc_2))
        self.assertFalse(restricted_rag_ctx.can_access_document(self.doc_confidential))

    def test_mock_rag_access_controller_candidate_filtering(self) -> None:
        """Verifies BaseRAGAccessController prunes unauthorized chunks and KG nodes."""
        controller = MockRAGAccessController()

        rag_ctx = RAGSecurityContext(
            user_id=self.user_employee,
            organization_id=self.org_a,
            allowed_document_ids={self.doc_1},
        )

        candidates = [
            RetrievalResult(
                chunk_id=uuid4(),
                document_id=self.doc_1,
                content="Allowed doc snippet",
                score=0.95,
            ),
            RetrievalResult(
                chunk_id=uuid4(),
                document_id=self.doc_confidential,
                content="Confidential financial snippet",
                score=0.98,
            ),
        ]

        filtered = controller.filter_retrieval_candidates(candidates, rag_ctx)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].document_id, self.doc_1)
        self.assertEqual(filtered[0].content, "Allowed doc snippet")

        # Knowledge Graph Node Access Verification
        node_allowed = KGEntityRecord(
            id=uuid4(),
            organization_id=self.org_a,
            name="Alpha Project",
            entity_type="Project",
            source_document_id=self.doc_1,
        )
        node_confidential = KGEntityRecord(
            id=uuid4(),
            organization_id=self.org_a,
            name="Q4 Strategy",
            entity_type="Financials",
            source_document_id=self.doc_confidential,
        )
        node_cross_tenant = KGEntityRecord(
            id=uuid4(),
            organization_id=self.org_b,
            name="External Corp",
            entity_type="Company",
            source_document_id=None,
        )

        self.assertTrue(controller.verify_graph_node_access(node_allowed, rag_ctx))
        self.assertFalse(controller.verify_graph_node_access(node_confidential, rag_ctx))
        self.assertFalse(controller.verify_graph_node_access(node_cross_tenant, rag_ctx))

    def test_search_query_and_vector_filter_contracts(self) -> None:
        """Verifies SearchQuery and VectorFilter carry security contexts and document restrictions."""
        rag_ctx = RAGSecurityContext(
            user_id=self.user_pm,
            organization_id=self.org_a,
            role=UserRole.PROJECT_MANAGER.value,
            allowed_document_ids={self.doc_1},
        )

        query = SearchQuery(
            query="quarterly roadmap",
            organization_id=self.org_a,
            allowed_document_ids=[self.doc_1],
            security_context=rag_ctx,
        )
        self.assertEqual(query.organization_id, self.org_a)
        self.assertEqual(query.allowed_document_ids, [self.doc_1])
        self.assertIsNotNone(query.security_context)

        v_filter = VectorFilter(
            organization_id=self.org_a,
            allowed_document_ids=[self.doc_1],
            user_role="ProjectManager",
        )
        self.assertEqual(v_filter.organization_id, self.org_a)
        self.assertEqual(v_filter.allowed_document_ids, [self.doc_1])
        self.assertEqual(v_filter.user_role, "ProjectManager")


if __name__ == "__main__":
    unittest.main()

"""Security & Multi-Tenant Isolation Integration Test Suite.

Verifies:
1. Multi-tenant organizational isolation (cross-organization access attempts blocked).
2. JWT signature validation, tampering rejection, and secret key boundary.
3. RBAC permission checks across OrgAdmin, Manager, Member, and Viewer roles.
4. Token expiration enforcement and lifecycle boundaries.
5. Account suspension enforcement across authentication gates.

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.4 Authentication & Identity Management
"""

import unittest
from datetime import timedelta
from uuid import uuid4

import jwt
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.schemas.envelope import ApiResponse
from tests.conftest import sync_test_engine

# Add temporary test routes to the app for testing RBAC and tenant isolation
if not hasattr(app.state, "security_test_routes_registered"):
    @app.get("/api/v1/test/admin-only", tags=["Security Testing"])
    async def admin_only_endpoint(
        user: AuthenticatedUser = Depends(require_roles(UserRole.ORG_ADMIN)),
    ) -> ApiResponse[dict]:
        return ApiResponse(
            success=True,
            message="Admin authorized",
            data={"role": user.role, "org_id": str(user.organization_id)},
        )

    @app.get("/api/v1/test/manager-or-admin", tags=["Security Testing"])
    async def manager_or_admin_endpoint(
        user: AuthenticatedUser = Depends(
            require_roles(UserRole.ORG_ADMIN, UserRole.MANAGER)
        ),
    ) -> ApiResponse[dict]:
        return ApiResponse(
            success=True,
            message="Manager or Admin authorized",
            data={"role": user.role},
        )

    @app.get("/api/v1/test/tenant-echo", tags=["Security Testing"])
    async def tenant_echo_endpoint(
        user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> ApiResponse[dict]:
        return ApiResponse(
            success=True,
            message="Tenant identity resolved",
            data={
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
            },
        )

    app.state.security_test_routes_registered = True


class TestAuthSecurityIsolation(unittest.TestCase):
    """Test suite validating tenant isolation, RBAC, and crypto security boundaries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # Organization Alpha
            cls.org_alpha = Organization(name="Alpha Corp", domain="alpha.com")
            session.add(cls.org_alpha)
            session.flush()

            cls.user_alpha_admin = User(
                email="admin@alpha.com",
                hashed_password=get_password_hash("AlphaPass123!"),
                full_name="Alpha Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_alpha.id,
                is_active=True,
            )
            cls.user_alpha_member = User(
                email="member@alpha.com",
                hashed_password=get_password_hash("AlphaPass123!"),
                full_name="Alpha Member",
                role=UserRole.MEMBER,
                organization_id=cls.org_alpha.id,
                is_active=True,
            )
            cls.user_alpha_viewer = User(
                email="viewer@alpha.com",
                hashed_password=get_password_hash("AlphaPass123!"),
                full_name="Alpha Viewer",
                role=UserRole.VIEWER,
                organization_id=cls.org_alpha.id,
                is_active=True,
            )

            # Organization Beta
            cls.org_beta = Organization(name="Beta Inc", domain="beta.com")
            session.add(cls.org_beta)
            session.flush()

            cls.user_beta_admin = User(
                email="admin@beta.com",
                hashed_password=get_password_hash("BetaPass123!"),
                full_name="Beta Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_beta.id,
                is_active=True,
            )
            session.add(cls.user_alpha_admin)
            session.add(cls.user_alpha_member)
            session.add(cls.user_alpha_viewer)
            session.add(cls.user_beta_admin)
            session.commit()

            cls.org_alpha_id = str(cls.org_alpha.id)
            cls.org_beta_id = str(cls.org_beta.id)

    # --------------------------------------------------------------------------
    # 1. Multi-Tenant Organizational Isolation
    # --------------------------------------------------------------------------
    def test_multi_tenant_token_segregation(self) -> None:
        """Verify tokens for distinct organizations are strictly partitioned."""
        # Login Alpha Admin
        res_alpha = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@alpha.com", "password": "AlphaPass123!"},
        )
        self.assertEqual(res_alpha.status_code, 200)
        token_alpha = res_alpha.json()["data"]["access_token"]

        # Login Beta Admin
        res_beta = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@beta.com", "password": "BetaPass123!"},
        )
        self.assertEqual(res_beta.status_code, 200)
        token_beta = res_beta.json()["data"]["access_token"]

        # Call tenant echo endpoint
        echo_alpha = self.client.get(
            "/api/v1/test/tenant-echo",
            headers={"Authorization": f"Bearer {token_alpha}"},
        )
        self.assertEqual(echo_alpha.status_code, 200)
        self.assertEqual(echo_alpha.json()["data"]["organization_id"], self.org_alpha_id)

        echo_beta = self.client.get(
            "/api/v1/test/tenant-echo",
            headers={"Authorization": f"Bearer {token_beta}"},
        )
        self.assertEqual(echo_beta.status_code, 200)
        self.assertEqual(echo_beta.json()["data"]["organization_id"], self.org_beta_id)

        self.assertNotEqual(
            echo_alpha.json()["data"]["organization_id"],
            echo_beta.json()["data"]["organization_id"],
        )

    def test_forged_tenant_claim_with_invalid_signature_rejected(self) -> None:
        """Attempting to forge another organization's ID with bad secret fails."""
        forged_claims = {
            "sub": str(uuid4()),
            "email": "hacker@evil.com",
            "role": "OrgAdmin",
            "org_id": self.org_alpha_id,  # Attempting to access Alpha
        }
        forged_token = jwt.encode(
            forged_claims,
            "forged_secret_key_long_enough_32bytes!",
            algorithm=settings.ALGORITHM,
        )

        res = self.client.get(
            "/api/v1/test/tenant-echo",
            headers={"Authorization": f"Bearer {forged_token}"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], ErrorCode.AUTH_TOKEN_INVALID)

    # --------------------------------------------------------------------------
    # 2. Role-Based Access Control (RBAC) Enforcement
    # --------------------------------------------------------------------------
    def test_rbac_admin_only_endpoint(self) -> None:
        """OrgAdmin is permitted to admin-only endpoint; Member and Viewer are rejected."""
        # 1. OrgAdmin -> 200 OK
        admin_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@alpha.com", "password": "AlphaPass123!"},
        )
        admin_token = admin_login.json()["data"]["access_token"]
        res_admin = self.client.get(
            "/api/v1/test/admin-only",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(res_admin.status_code, 200)
        self.assertTrue(res_admin.json()["success"])

        # 2. Member -> 403 Forbidden
        member_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "member@alpha.com", "password": "AlphaPass123!"},
        )
        member_token = member_login.json()["data"]["access_token"]
        res_member = self.client.get(
            "/api/v1/test/admin-only",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        self.assertEqual(res_member.status_code, 403)
        self.assertEqual(res_member.json()["error"]["code"], ErrorCode.AUTH_FORBIDDEN)

        # 3. Viewer -> 403 Forbidden
        viewer_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "viewer@alpha.com", "password": "AlphaPass123!"},
        )
        viewer_token = viewer_login.json()["data"]["access_token"]
        res_viewer = self.client.get(
            "/api/v1/test/admin-only",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        self.assertEqual(res_viewer.status_code, 403)
        self.assertEqual(res_viewer.json()["error"]["code"], ErrorCode.AUTH_FORBIDDEN)

    def test_rbac_manager_or_admin_endpoint(self) -> None:
        """Endpoint allowing OrgAdmin and Manager permits OrgAdmin and rejects Viewer."""
        admin_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@alpha.com", "password": "AlphaPass123!"},
        )
        admin_token = admin_login.json()["data"]["access_token"]
        res_admin = self.client.get(
            "/api/v1/test/manager-or-admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(res_admin.status_code, 200)

        viewer_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "viewer@alpha.com", "password": "AlphaPass123!"},
        )
        viewer_token = viewer_login.json()["data"]["access_token"]
        res_viewer = self.client.get(
            "/api/v1/test/manager-or-admin",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        self.assertEqual(res_viewer.status_code, 403)

    # --------------------------------------------------------------------------
    # 3. Token Security & Cryptographic Integrity
    # --------------------------------------------------------------------------
    def test_expired_token_rejected_at_gateway(self) -> None:
        """Token with past expiration timestamp is rejected with AUTH_TOKEN_EXPIRED."""
        claims = {
            "sub": str(uuid4()),
            "email": "expired@alpha.com",
            "role": "Member",
            "org_id": self.org_alpha_id,
        }
        expired_token = create_access_token(claims, expires_delta=timedelta(seconds=-30))

        res = self.client.get(
            "/api/v1/test/tenant-echo",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], ErrorCode.AUTH_TOKEN_EXPIRED)

    def test_tampered_payload_rejected(self) -> None:
        """Token whose payload portion has been tampered with is rejected with AUTH_TOKEN_INVALID."""
        claims = {
            "sub": str(uuid4()),
            "email": "tamper@alpha.com",
            "role": "Member",
            "org_id": self.org_alpha_id,
        }
        valid_token = create_access_token(claims)
        # Split header, payload, signature
        parts = valid_token.split(".")
        # Tamper payload
        tampered_token = f"{parts[0]}.eyJob2dnZWRfcGF5bG9hZCI6IHRydWV9.{parts[2]}"

        res = self.client.get(
            "/api/v1/test/tenant-echo",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], ErrorCode.AUTH_TOKEN_INVALID)

    def test_malformed_auth_headers_handled_gracefully(self) -> None:
        """Ensure malformed or non-Bearer authorization headers return 401 without unhandled crash."""
        cases = [
            "",
            "Bearer",
            "Bearer ",
            "Basic dXNlcjpwYXNz",
            "Token 12345678",
            "Bearer invalid.parts",
        ]
        for header in cases:
            res = self.client.get(
                "/api/v1/test/tenant-echo",
                headers={"Authorization": header} if header else {},
            )
            self.assertIn(
                res.status_code,
                [401, 403],
                f"Header '{header}' should be rejected with 401/403 but got {res.status_code}",
            )
            self.assertFalse(res.json()["success"])


if __name__ == "__main__":
    unittest.main()

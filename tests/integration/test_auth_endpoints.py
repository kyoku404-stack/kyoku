"""Integration Test Suite: Phase 1.4 Authentication Endpoints.

Verifies the complete HTTP API lifecycle for all 8 authentication endpoints:
1. POST /api/v1/auth/register (User registration, auto-tenant creation, duplication rejection)
2. POST /api/v1/auth/login (Credential validation, JWT double-token issuance, suspended account prevention)
3. POST /api/v1/auth/refresh (Refresh token verification, new access token generation, invalid token handling)
4. GET  /api/v1/auth/me (Authenticated profile resolution, unauthorized rejection)
5. POST /api/v1/auth/logout (Session termination, authentication requirement)
6. POST /api/v1/auth/forgot-password (Password reset initiation, email enumeration protection)
7. POST /api/v1/auth/reset-password (Password reset execution, validation constraints)
8. PATCH /api/v1/auth/change-password (Authenticated password update, old password rejection)

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.4 Authentication & Identity Management
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAuthEndpointsIntegration(unittest.TestCase):
    """Integration test suite for authentication endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        # Seed dedicated test tenant and user in SQLite sync session
        with Session(sync_test_engine) as session:
            cls.test_org = Organization(
                name="Auth Test Corp",
                domain="authtest.com",
            )
            session.add(cls.test_org)
            session.flush()

            cls.active_user = User(
                email="auth.active@authtest.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Active Test User",
                role=UserRole.MEMBER,
                organization_id=cls.test_org.id,
                is_active=True,
            )
            cls.suspended_user = User(
                email="auth.suspended@authtest.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Suspended User",
                role=UserRole.MEMBER,
                organization_id=cls.test_org.id,
                is_active=False,
            )
            session.add(cls.active_user)
            session.add(cls.suspended_user)
            session.commit()

            cls.org_id = str(cls.test_org.id)

    # --------------------------------------------------------------------------
    # 1. Registration (/api/v1/auth/register)
    # --------------------------------------------------------------------------
    def test_register_new_user_with_explicit_organization(self) -> None:
        """Registering a new user with valid org ID should succeed with 201."""
        unique_email = f"user_{uuid4().hex[:8]}@authtest.com"
        payload = {
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "New Registered User",
            "organization_id": self.org_id,
            "role": "Member",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["email"], unique_email)
        self.assertEqual(body["data"]["role"], "Member")
        self.assertEqual(body["data"]["organization_id"], self.org_id)

    def test_register_new_user_without_org_id_creates_domain_org(self) -> None:
        """Registering with domain auto-provisions organization and grants OrgAdmin."""
        unique_suffix = uuid4().hex[:6]
        email = f"lead_{unique_suffix}@innovate{unique_suffix}.com"
        payload = {
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Domain Founder",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["email"], email)
        self.assertEqual(body["data"]["role"], UserRole.ORG_ADMIN)
        self.assertIsNotNone(body["data"]["organization_id"])

    def test_register_duplicate_email_fails(self) -> None:
        """Registering with an already-existing email must return 409 Conflict."""
        payload = {
            "email": "auth.active@authtest.com",
            "password": "SecurePassword123!",
            "full_name": "Duplicate User",
            "organization_id": self.org_id,
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
        self.assertEqual(res.status_code, 409)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_EMAIL_EXISTS)

    def test_register_nonexistent_org_id_fails(self) -> None:
        """Registering with a non-existent org UUID returns 404 NotFound."""
        payload = {
            "email": f"orphan_{uuid4().hex[:6]}@nowhere.com",
            "password": "SecurePassword123!",
            "full_name": "Orphan User",
            "organization_id": str(uuid4()),
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
        self.assertEqual(res.status_code, 404)

    def test_register_validation_error(self) -> None:
        """Invalid email or short password returns 422 Unprocessable Entity."""
        payload = {
            "email": "not-an-email",
            "password": "short",
            "full_name": "",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
        self.assertEqual(res.status_code, 422)

    # --------------------------------------------------------------------------
    # 2. Login (/api/v1/auth/login)
    # --------------------------------------------------------------------------
    def test_login_success(self) -> None:
        """Valid credentials return 200, JWT tokens, and user profile."""
        payload = {
            "email": "auth.active@authtest.com",
            "password": "Password123!",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("access_token", body["data"])
        self.assertIn("refresh_token", body["data"])
        self.assertEqual(body["data"]["token_type"], "bearer")
        self.assertGreater(body["data"]["expires_in"], 0)
        self.assertEqual(body["data"]["user"]["email"], "auth.active@authtest.com")

    def test_login_invalid_password(self) -> None:
        """Incorrect password returns 401 with AUTH_INVALID_CREDENTIALS."""
        payload = {
            "email": "auth.active@authtest.com",
            "password": "WrongPassword999!",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_INVALID_CREDENTIALS)

    def test_login_unregistered_email(self) -> None:
        """Unregistered email returns 401 with AUTH_INVALID_CREDENTIALS."""
        payload = {
            "email": "nonexistent@authtest.com",
            "password": "Password123!",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_INVALID_CREDENTIALS)

    def test_login_suspended_account_fails(self) -> None:
        """Suspended user login returns 401 with AUTH_ACCOUNT_DISABLED."""
        payload = {
            "email": "auth.suspended@authtest.com",
            "password": "Password123!",
        }
        res = self.client.post(f"{settings.API_V1_STR}/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_ACCOUNT_DISABLED)

    # --------------------------------------------------------------------------
    # 3. Refresh Token (/api/v1/auth/refresh)
    # --------------------------------------------------------------------------
    def test_refresh_token_success(self) -> None:
        """Valid refresh token returns new access token."""
        claims = {
            "sub": str(uuid4()),
            "email": "refresher@authtest.com",
            "role": "Member",
            "org_id": self.org_id,
        }
        refresh_tok = create_refresh_token(claims)

        res = self.client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh_tok},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("access_token", body["data"])
        self.assertEqual(body["data"]["token_type"], "bearer")

    def test_refresh_token_with_access_token_fails(self) -> None:
        """Supplying an access token to the refresh endpoint fails with AUTH_TOKEN_INVALID."""
        claims = {
            "sub": str(uuid4()),
            "email": "user@authtest.com",
            "role": "Member",
            "org_id": self.org_id,
        }
        access_tok = create_access_token(claims)

        res = self.client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": access_tok},
        )
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_TOKEN_INVALID)

    def test_refresh_token_invalid_string(self) -> None:
        """Malformed refresh token string returns 401 AUTH_TOKEN_INVALID."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": "malformed_token_string"},
        )
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_TOKEN_INVALID)

    # --------------------------------------------------------------------------
    # 4. Current User Profile (/api/v1/auth/me)
    # --------------------------------------------------------------------------
    def test_get_me_success(self) -> None:
        """Authenticated request to /auth/me returns user profile."""
        login_res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "auth.active@authtest.com", "password": "Password123!"},
        )
        token = login_res.json()["data"]["access_token"]

        res = self.client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["email"], "auth.active@authtest.com")
        self.assertEqual(body["data"]["full_name"], "Active Test User")

    def test_get_me_missing_token_fails(self) -> None:
        """Request without Authorization header returns 401 AUTH_UNAUTHORIZED."""
        res = self.client.get(f"{settings.API_V1_STR}/auth/me")
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_UNAUTHORIZED)

    def test_get_me_invalid_token_fails(self) -> None:
        """Request with invalid Bearer token returns 401 AUTH_TOKEN_INVALID."""
        res = self.client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"},
        )
        self.assertEqual(res.status_code, 401)
        body = res.json()
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_TOKEN_INVALID)

    # --------------------------------------------------------------------------
    # 5. Logout (/api/v1/auth/logout)
    # --------------------------------------------------------------------------
    def test_logout_success(self) -> None:
        """Authenticated request to /auth/logout returns 200."""
        login_res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "auth.active@authtest.com", "password": "Password123!"},
        )
        token = login_res.json()["data"]["access_token"]

        res = self.client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

    def test_logout_unauthenticated_fails(self) -> None:
        """Unauthenticated logout request returns 401."""
        res = self.client.post(f"{settings.API_V1_STR}/auth/logout", json={})
        self.assertEqual(res.status_code, 401)

    # --------------------------------------------------------------------------
    # 6. Password Reset Flow (/api/v1/auth/forgot-password, /api/v1/auth/reset-password)
    # --------------------------------------------------------------------------
    def test_forgot_password_success(self) -> None:
        """Requesting password reset returns 200 whether email exists or not."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": "auth.active@authtest.com"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        res_unknown = self.client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": "unknown@authtest.com"},
        )
        self.assertEqual(res_unknown.status_code, 200)
        self.assertTrue(res_unknown.json()["success"])

    def test_reset_password_success(self) -> None:
        """Resetting password with valid token format returns 200."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/reset-password",
            json={"token": "reset_token_test_123", "new_password": "NewSecurePassword456!"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    # --------------------------------------------------------------------------
    # 7. Change Password (/api/v1/auth/change-password)
    # --------------------------------------------------------------------------
    def test_change_password_workflow(self) -> None:
        """Authenticated password change succeeds and updates credentials."""
        # 1. Register a dedicated user for password change
        unique_email = f"pwd_change_{uuid4().hex[:6]}@authtest.com"
        reg_res = self.client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": unique_email,
                "password": "InitialPassword123!",
                "full_name": "Password Changer",
                "organization_id": self.org_id,
            },
        )
        self.assertEqual(reg_res.status_code, 201)

        # 2. Login to get token
        login_res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": unique_email, "password": "InitialPassword123!"},
        )
        token = login_res.json()["data"]["access_token"]

        # 3. Attempt with incorrect current password -> returns 401
        bad_change = self.client.patch(
            f"{settings.API_V1_STR}/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongInitialPassword!",
                "new_password": "UpdatedPassword456!",
            },
        )
        self.assertEqual(bad_change.status_code, 401)
        self.assertEqual(bad_change.json()["error"]["code"], ErrorCode.AUTH_INVALID_CREDENTIALS)

        # 4. Change password with correct current password
        good_change = self.client.patch(
            f"{settings.API_V1_STR}/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "InitialPassword123!",
                "new_password": "UpdatedPassword456!",
            },
        )
        self.assertEqual(good_change.status_code, 200)

        # 5. Old password no longer works
        old_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": unique_email, "password": "InitialPassword123!"},
        )
        self.assertEqual(old_login.status_code, 401)

        # 6. New password works successfully
        new_login = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": unique_email, "password": "UpdatedPassword456!"},
        )
        self.assertEqual(new_login.status_code, 200)


if __name__ == "__main__":
    unittest.main()

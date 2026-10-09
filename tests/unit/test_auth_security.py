"""Unit Tests for Authentication Security, Cryptography, JWT Lifecycle & RBAC.

Verifies:
1. Password hashing with bcrypt, unique random salting, and verification.
2. JWT access and refresh token creation, claims verification, and expiration delta.
3. JWT token decoding, tampering detection, and expired token rejection.
4. FastApi auth dependencies: get_current_user, get_current_active_user, require_roles.
5. Auth settings configuration and secret management.

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.4 Authentication & Identity Management
"""

import asyncio
import unittest
from datetime import timedelta
from uuid import uuid4

import jwt

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    get_current_user,
    require_roles,
)
from backend.app.core.config import Settings, settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import ForbiddenException, UnauthorizedException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordSecurity(unittest.TestCase):
    """Unit tests for password cryptographic operations."""

    def test_password_hashing_and_verification(self) -> None:
        """Test secure hashing and verification of plain passwords."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith("$2b$"), "Bcrypt hash should start with $2b$")
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword123!", hashed))

    def test_password_hashing_uniqueness_with_salt(self) -> None:
        """Test that identical passwords generate distinct hashes due to random salting."""
        password = "SameCorporatePassword2026!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        self.assertNotEqual(hash1, hash2, "Bcrypt hashes with distinct salts must not match")
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))

    def test_password_verification_invalid_inputs(self) -> None:
        """Test password verification gracefully handles corrupt hashes without throwing."""
        self.assertFalse(verify_password("Password123!", "not_a_bcrypt_hash"))
        self.assertFalse(verify_password("Password123!", ""))
        self.assertFalse(verify_password("", "garbage_data"))

    def test_special_characters_and_unicode_password(self) -> None:
        """Test handling of Unicode characters and symbols in passwords."""
        password = "🔒K€€p_S€cur1ty_P@ssw0rd!_日本語"
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("🔒K€€p_S€cur1ty_P@ssw0rd!_English", hashed))


class TestJwtTokenSecurity(unittest.TestCase):
    """Unit tests for JWT token generation, claims validation, and tampering checks."""

    def setUp(self) -> None:
        self.user_id = uuid4()
        self.org_id = uuid4()
        self.claims = {
            "sub": str(self.user_id),
            "email": "devops@enterprise.com",
            "role": UserRole.ORG_ADMIN,
            "org_id": str(self.org_id),
        }

    def test_create_access_token_claims_and_type(self) -> None:
        """Test access token structure, claims, and type attribute."""
        token = create_access_token(self.claims)
        payload = decode_token(token)

        self.assertEqual(payload["sub"], str(self.user_id))
        self.assertEqual(payload["email"], "devops@enterprise.com")
        self.assertEqual(payload["role"], UserRole.ORG_ADMIN)
        self.assertEqual(payload["org_id"], str(self.org_id))
        self.assertEqual(payload["type"], "access")
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

    def test_create_refresh_token_claims_and_type(self) -> None:
        """Test refresh token structure and type attribute."""
        token = create_refresh_token(self.claims)
        payload = decode_token(token)

        self.assertEqual(payload["sub"], str(self.user_id))
        self.assertEqual(payload["type"], "refresh")

    def test_access_token_custom_expiry(self) -> None:
        """Test access token creation with custom timedelta."""
        delta = timedelta(minutes=15)
        token = create_access_token(self.claims, expires_delta=delta)
        payload = decode_token(token)

        # Token expiration should be approximately 15 minutes ahead of issued at
        self.assertAlmostEqual(payload["exp"] - payload["iat"], 900, delta=5)

    def test_decode_expired_token_raises_exception(self) -> None:
        """Test that expired tokens raise UnauthorizedException with AUTH_TOKEN_EXPIRED."""
        # Create token already expired in the past
        past_delta = timedelta(seconds=-10)
        token = create_access_token(self.claims, expires_delta=past_delta)

        with self.assertRaises(UnauthorizedException) as ctx:
            decode_token(token)

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_EXPIRED)

    def test_decode_invalid_signature_raises_exception(self) -> None:
        """Test that tokens signed with a different key are rejected with AUTH_TOKEN_INVALID."""
        tampered_token = jwt.encode(
            self.claims,
            "foreign_unauthorized_secret_key_32_bytes_long!",
            algorithm=settings.ALGORITHM,
        )

        with self.assertRaises(UnauthorizedException) as ctx:
            decode_token(tampered_token)

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_INVALID)

    def test_decode_malformed_token_raises_exception(self) -> None:
        """Test that malformed token strings raise UnauthorizedException with AUTH_TOKEN_INVALID."""
        with self.assertRaises(UnauthorizedException) as ctx:
            decode_token("not.a.valid.jwt.token.string")

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_INVALID)


class TestAuthDependenciesAndRbac(unittest.TestCase):
    """Unit tests for FastAPI authentication dependencies and RBAC filters."""

    def setUp(self) -> None:
        self.user_id = uuid4()
        self.org_id = uuid4()

    def test_get_current_user_valid_token(self) -> None:
        """Test extracting AuthenticatedUser from valid access token."""
        token = create_access_token(
            {
                "sub": str(self.user_id),
                "email": "user@enterprise.com",
                "role": UserRole.MEMBER,
                "org_id": str(self.org_id),
                "is_active": True,
            }
        )

        current_user = asyncio.run(get_current_user(token=token))
        self.assertIsInstance(current_user, AuthenticatedUser)
        self.assertEqual(current_user.id, self.user_id)
        self.assertEqual(current_user.email, "user@enterprise.com")
        self.assertEqual(current_user.role, UserRole.MEMBER)
        self.assertEqual(current_user.organization_id, self.org_id)
        self.assertTrue(current_user.is_active)

    def test_get_current_user_missing_token_raises_unauthorized(self) -> None:
        """Test that missing authorization token raises UnauthorizedException."""
        with self.assertRaises(UnauthorizedException) as ctx:
            asyncio.run(get_current_user(token=None))

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_UNAUTHORIZED)

    def test_get_current_user_missing_claims_raises_invalid(self) -> None:
        """Test token missing essential claims (sub or email) raises AUTH_TOKEN_INVALID."""
        token = create_access_token({"role": "Member"})  # Missing sub and email

        with self.assertRaises(UnauthorizedException) as ctx:
            asyncio.run(get_current_user(token=token))

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_INVALID)

    def test_get_current_user_invalid_uuid_raises_invalid(self) -> None:
        """Test token containing malformed UUID raises AUTH_TOKEN_INVALID."""
        token = create_access_token(
            {
                "sub": "not-a-valid-uuid",
                "email": "valid@enterprise.com",
                "role": "Member",
            }
        )

        with self.assertRaises(UnauthorizedException) as ctx:
            asyncio.run(get_current_user(token=token))

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_INVALID)

    def test_get_current_active_user_active_passes(self) -> None:
        """Test active user passes active check."""
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="active@enterprise.com",
            role=UserRole.MEMBER,
            organization_id=self.org_id,
            is_active=True,
        )
        res = asyncio.run(get_current_active_user(current_user=user))
        self.assertEqual(res.id, self.user_id)

    def test_get_current_active_user_inactive_raises_forbidden(self) -> None:
        """Test deactivated/suspended user raises ForbiddenException with AUTH_FORBIDDEN."""
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="inactive@enterprise.com",
            role=UserRole.MEMBER,
            organization_id=self.org_id,
            is_active=False,
        )

        with self.assertRaises(ForbiddenException) as ctx:
            asyncio.run(get_current_active_user(current_user=user))

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_FORBIDDEN)

    def test_require_roles_allows_authorized_role(self) -> None:
        """Test require_roles allows user with matching permission."""
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="admin@enterprise.com",
            role=UserRole.ORG_ADMIN,
            organization_id=self.org_id,
            is_active=True,
        )

        checker = require_roles(UserRole.ORG_ADMIN, UserRole.MANAGER)
        res = asyncio.run(checker(current_user=user))
        self.assertEqual(res.id, self.user_id)

    def test_require_roles_rejects_unauthorized_role(self) -> None:
        """Test require_roles raises ForbiddenException when role is insufficient."""
        user = AuthenticatedUser(
            user_id=self.user_id,
            email="viewer@enterprise.com",
            role=UserRole.VIEWER,
            organization_id=self.org_id,
            is_active=True,
        )

        checker = require_roles(UserRole.ORG_ADMIN)
        with self.assertRaises(ForbiddenException) as ctx:
            asyncio.run(checker(current_user=user))

        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_FORBIDDEN)


class TestAuthSettingsConfiguration(unittest.TestCase):
    """Unit tests for Auth environment variables and cryptography settings."""

    def test_auth_settings_defaults(self) -> None:
        """Verify default security configuration settings."""
        self.assertEqual(settings.ALGORITHM, "HS256")
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertGreater(settings.ACCESS_TOKEN_EXPIRE_MINUTES, 0)

    def test_auth_custom_settings_override(self) -> None:
        """Verify custom security settings initialization."""
        custom_settings = Settings(
            SECRET_KEY="custom_super_secure_key_12345",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            DATABASE_URL=None,
            SYNC_DATABASE_URL=None,
        )
        self.assertEqual(custom_settings.SECRET_KEY, "custom_super_secure_key_12345")
        self.assertEqual(custom_settings.ACCESS_TOKEN_EXPIRE_MINUTES, 30)


if __name__ == "__main__":
    unittest.main()

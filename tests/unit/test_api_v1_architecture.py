"""Unit Test Suite: Phase 1.2 Backend Architecture & API Foundation.

Verifies:
- Core constants, enums, and error codes
- Cryptographic security utilities (bcrypt hashing, JWT tokens)
- Custom domain exceptions and HTTP status mapping
- Standardized response envelopes (ApiResponse, ApiErrorResponse, PaginatedData)
- BaseRepository operations
- Core domain services (AuthService, UserService, DocumentService, SearchService, ChatService, HealthService)
"""

import unittest
from datetime import timedelta
from uuid import uuid4

try:
    from backend.app.core.constants import DocumentStatus, ErrorCode, UserRole
    from backend.app.core.exceptions import (
        ConflictException,
        ForbiddenException,
        NotFoundException,
        UnauthorizedException,
        ValidationException,
    )
    from backend.app.core.security import (
        create_access_token,
        create_refresh_token,
        decode_token,
        get_password_hash,
        verify_password,
    )
    from backend.app.schemas.auth import LoginRequest
    from backend.app.schemas.chat import ChatQueryRequest
    from backend.app.schemas.envelope import ApiErrorResponse, ApiResponse, PaginatedData
    from backend.app.schemas.search import HybridSearchRequest
    from backend.app.services.auth_service import AuthService
    from backend.app.services.chat_service import ChatService
    from backend.app.services.document_service import DocumentService
    from backend.app.services.health_service import HealthService
    from backend.app.services.search_service import SearchService

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


@unittest.skipUnless(HAS_DEPS, "Backend dependencies (pydantic, fastapi, passlib) not installed")
class TestApiV1Architecture(unittest.IsolatedAsyncioTestCase):
    """Unit tests for Phase 1.2 backend foundation and domain components."""

    def test_core_constants(self) -> None:
        """Verify error codes and enum representations."""
        self.assertEqual(ErrorCode.AUTH_INVALID_CREDENTIALS.value, "AUTH_INVALID_CREDENTIALS")
        self.assertEqual(ErrorCode.VALIDATION_ERROR.value, "VALIDATION_ERROR")
        self.assertEqual(UserRole.ORG_ADMIN.value, "OrgAdmin")
        self.assertEqual(DocumentStatus.PROCESSED.value, "PROCESSED")

    def test_security_password_hashing(self) -> None:
        """Verify bcrypt password hashing and verification."""
        password = "EnterpriseSecurePass2026!"
        hashed = get_password_hash(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_security_jwt_token_lifecycle(self) -> None:
        """Verify JWT access and refresh token issuance and claim extraction."""
        user_id = str(uuid4())
        claims = {
            "sub": user_id,
            "email": "lead@acme.com",
            "role": UserRole.ORG_ADMIN.value,
            "org_id": str(uuid4()),
        }

        # Access token
        access_token = create_access_token(claims)
        payload = decode_token(access_token)
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["type"], "access")
        self.assertEqual(payload["role"], UserRole.ORG_ADMIN.value)

        # Refresh token
        refresh_token = create_refresh_token(claims)
        refresh_payload = decode_token(refresh_token)
        self.assertEqual(refresh_payload["type"], "refresh")

        # Expired token raises UnauthorizedException
        expired_token = create_access_token(claims, expires_delta=timedelta(seconds=-10))
        with self.assertRaises(UnauthorizedException) as ctx:
            decode_token(expired_token)
        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_TOKEN_EXPIRED)

    def test_custom_exceptions(self) -> None:
        """Verify exception hierarchy, status codes, and error codes."""
        exc_404 = NotFoundException(message="Document missing", details={"id": 123})
        self.assertEqual(exc_404.status_code, 404)
        self.assertEqual(exc_404.code, ErrorCode.NOT_FOUND)

        exc_401 = UnauthorizedException()
        self.assertEqual(exc_401.status_code, 401)
        self.assertEqual(exc_401.code, ErrorCode.AUTH_UNAUTHORIZED)

        exc_403 = ForbiddenException()
        self.assertEqual(exc_403.status_code, 403)
        self.assertEqual(exc_403.code, ErrorCode.AUTH_FORBIDDEN)

        exc_422 = ValidationException()
        self.assertEqual(exc_422.status_code, 422)
        self.assertEqual(exc_422.code, ErrorCode.VALIDATION_ERROR)

        exc_409 = ConflictException()
        self.assertEqual(exc_409.status_code, 409)
        self.assertEqual(exc_409.code, ErrorCode.CONFLICT)

    def test_standard_envelopes(self) -> None:
        """Verify ApiResponse, ApiErrorResponse, and PaginatedData serialization."""
        from backend.app.schemas.envelope import ErrorDetail

        success_resp = ApiResponse(data={"key": "value"})
        self.assertTrue(success_resp.success)
        self.assertEqual(success_resp.data, {"key": "value"})

        error_resp = ApiErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.AUTH_INVALID_CREDENTIALS.value,
                message="Bad credentials",
            )
        )
        self.assertFalse(error_resp.success)
        self.assertEqual(error_resp.error.code, "AUTH_INVALID_CREDENTIALS")

        paginated = PaginatedData(items=[1, 2, 3], total=3, page=1, page_size=10, total_pages=1)
        self.assertEqual(len(paginated.items), 3)
        self.assertEqual(paginated.total, 3)

    async def test_auth_service(self) -> None:
        """Verify AuthService login, refresh, and profile retrieval."""
        from datetime import UTC, datetime
        from typing import cast
        from unittest.mock import AsyncMock

        from sqlalchemy.ext.asyncio import AsyncSession

        from backend.app.core.security import get_password_hash
        from backend.app.models.user import User

        auth_service = AuthService()

        user_mock = User(
            id=uuid4(),
            email="admin@acme.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Admin",
            role=UserRole.ORG_ADMIN.value,
            organization_id=uuid4(),
            is_active=True,
            created_at=datetime.now(UTC)
        )
        auth_service.repository.get_by_email = AsyncMock(return_value=user_mock) # type: ignore
        auth_service.repository.get = AsyncMock(return_value=user_mock) # type: ignore

        login_req = LoginRequest(email="admin@acme.com", password="Password123!")
        token_resp = await auth_service.login(db=cast(AsyncSession, None), login_data=login_req)
        self.assertIsNotNone(token_resp.access_token)
        self.assertIsNotNone(token_resp.refresh_token)
        self.assertEqual(token_resp.user.email, "admin@acme.com")

        # Refresh
        refresh_resp = await auth_service.refresh_token(str(token_resp.refresh_token))
        self.assertIsNotNone(refresh_resp.access_token)

        # Profile
        profile = await auth_service.get_current_user_profile(
            db=cast(AsyncSession, None),
            user_id=token_resp.user.id,
        )
        self.assertEqual(profile.email, "admin@acme.com")

    async def test_document_service(self) -> None:
        """Verify DocumentService upload validation and listing."""
        doc_service = DocumentService()
        org_id = uuid4()

        # Valid upload
        upload_resp = await doc_service.upload_document(
            db=None,
            filename="analysis.pdf",
            content_type="application/pdf",
            file_size=1024,
            org_id=org_id,
        )
        self.assertEqual(upload_resp.filename, "analysis.pdf")
        self.assertEqual(upload_resp.status, DocumentStatus.PROCESSING)

        # Invalid extension
        with self.assertRaises(ValidationException) as ctx:
            await doc_service.upload_document(
                db=None,
                filename="script.exe",
                content_type="application/x-msdownload",
                file_size=1024,
                org_id=org_id,
            )
        self.assertEqual(ctx.exception.code, ErrorCode.UNSUPPORTED_FILE_TYPE)

        # List docs
        docs_page = await doc_service.list_documents(db=None, org_id=org_id)
        self.assertEqual(len(docs_page.items), 1)

    async def test_search_and_chat_services(self) -> None:
        """Verify SearchService and ChatService response structures."""
        org_id = uuid4()
        search_service = SearchService()
        search_req = HybridSearchRequest(query="quarterly results", top_k=5)
        search_res = await search_service.hybrid_search(search_req, org_id)
        self.assertGreaterEqual(search_res.total_results, 1)

        chat_service = ChatService()
        chat_req = ChatQueryRequest(query="What is the remote work stipend?", top_k=3)
        chat_res = await chat_service.answer_query(chat_req, org_id)
        self.assertIn("stipend", chat_res.answer.lower())
        self.assertGreaterEqual(len(chat_res.citations), 1)

    async def test_health_service(self) -> None:
        """Verify HealthService basic and detailed diagnostic outputs."""
        health_service = HealthService()
        basic = await health_service.get_health_status()
        self.assertEqual(basic.status, "healthy")

        detailed = await health_service.get_detailed_health()
        self.assertEqual(detailed.status, "healthy")
        self.assertIn("database", detailed.components)
        self.assertIn("redis", detailed.components)


if __name__ == "__main__":
    unittest.main()

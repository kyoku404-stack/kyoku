"""Unit tests for Phase 1.10 Production Backend Configuration & Security Hardening.

Specification Source: devdocs/p1/p1.10.txt (Chapters 6, 9, 11, 15, 18)
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
Role: Member 2 (Backend Lead)
"""

import pytest
from starlette.requests import Request
from starlette.responses import Response

from backend.app.api.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.core.config import Settings
from backend.app.db.session import check_database_readiness, close_async_engine


class TestProductionSettingsEnvironment:
    """Verifies environment tier helpers and default production settings."""

    def test_environment_helpers_development(self) -> None:
        """Verifies development environment boolean properties."""
        s = Settings(ENVIRONMENT="development")
        assert s.is_development
        assert not s.is_production
        assert not s.is_staging
        assert not s.is_testing

    def test_environment_helpers_production(self) -> None:
        """Verifies production environment boolean properties."""
        s = Settings(ENVIRONMENT="production")
        assert s.is_production
        assert not s.is_development
        assert not s.is_staging
        assert not s.is_testing

    def test_environment_helpers_staging(self) -> None:
        """Verifies staging environment boolean properties."""
        s = Settings(ENVIRONMENT="staging")
        assert s.is_staging
        assert not s.is_production
        assert not s.is_development

    def test_environment_helpers_testing(self) -> None:
        """Verifies testing environment boolean properties."""
        s = Settings(ENVIRONMENT="testing")
        assert s.is_testing
        assert not s.is_production


class TestProductionDatabasePoolConfig:
    """Verifies configurable database pool parameters for high-concurrency production."""

    def test_default_database_pool_parameters(self) -> None:
        """Ensures production database pool parameters adhere to Phase 1.10 specs."""
        s = Settings()
        assert s.DB_POOL_SIZE >= 10
        assert s.DB_MAX_OVERFLOW >= 10
        assert s.DB_POOL_TIMEOUT == 30
        assert s.DB_POOL_RECYCLE == 1800
        assert s.DB_POOL_PRE_PING is True
        assert s.DB_STATEMENT_TIMEOUT_MS == 30000

    def test_custom_database_pool_overrides(self) -> None:
        """Ensures database pool parameters can be overridden via environment."""
        s = Settings(
            DB_POOL_SIZE=30,
            DB_MAX_OVERFLOW=15,
            DB_POOL_TIMEOUT=45,
            DB_POOL_RECYCLE=3600,
            DB_STATEMENT_TIMEOUT_MS=60000,
        )
        assert s.DB_POOL_SIZE == 30
        assert s.DB_MAX_OVERFLOW == 15
        assert s.DB_POOL_TIMEOUT == 45
        assert s.DB_POOL_RECYCLE == 3600
        assert s.DB_STATEMENT_TIMEOUT_MS == 60000


class TestProductionSecurityValidation:
    """Verifies production configuration validator catches insecure configurations."""

    def test_default_dev_secret_in_prod_triggers_critical_alert(self) -> None:
        """Alerts when default development SECRET_KEY is used in production."""
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="super_secret_keep_key_replace_in_production_2026",
        )
        warnings = s.validate_production_configuration()
        assert any("Default development SECRET_KEY detected" in w for w in warnings)

    def test_short_secret_in_prod_triggers_critical_alert(self) -> None:
        """Alerts when SECRET_KEY is shorter than 32 characters in production."""
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short_key_12345",
        )
        warnings = s.validate_production_configuration()
        assert any(">= 32 characters" in w for w in warnings)

    def test_localhost_db_in_prod_triggers_warning(self) -> None:
        """Warns when production DATABASE_URL references localhost."""
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/keep_db",
        )
        warnings = s.validate_production_configuration()
        assert any("local loopback" in w for w in warnings)

    def test_valid_production_configuration_clean(self) -> None:
        """Passes with zero warnings when configured with robust production parameters."""
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="cryptographically_secure_random_production_secret_key_2026",
            DATABASE_URL="postgresql+asyncpg://keep_prod:secure_pass@postgres-primary:5432/keep_db",
        )
        warnings = s.validate_production_configuration()
        assert len(warnings) == 0


class TestSecurityHeadersMiddleware:
    """Verifies SecurityHeadersMiddleware adds mandatory defense-in-depth headers."""

    @pytest.mark.asyncio
    async def test_security_headers_injected_development(self) -> None:
        """Ensures standard security headers are present in development."""
        middleware = SecurityHeadersMiddleware(app=None)  # type: ignore[arg-type]

        async def dummy_call_next(req: Request) -> Response:
            return Response(content="ok", media_type="text/plain")

        req = Request(scope={"type": "http", "method": "GET", "path": "/"})
        response = await middleware.dispatch(req, dummy_call_next)

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "geolocation=()" in response.headers["Permissions-Policy"]


class TestDatabaseSessionLifecycle:
    """Verifies database engine shutdown and readiness helpers."""

    def test_session_lifecycle_callables_exist(self) -> None:
        """Verifies lifecycle helpers are defined and callable."""
        assert callable(close_async_engine)
        assert callable(check_database_readiness)

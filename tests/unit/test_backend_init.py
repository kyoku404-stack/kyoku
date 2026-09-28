"""Unit tests for Phase 1.1 Backend Initialization & Database Setup.

Verifies:
- Settings parsing and validation
- Structured logging initialization
- Database Base and Mixin models
- FastAPI app instance, middleware, and health check endpoints
"""

import unittest
from datetime import datetime, timezone
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from backend.app.core.config import Settings
from backend.app.core.logging import setup_logging, get_logger
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.main import app


class MockItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Mock model to test DeclarativeBase and mixins."""
    __tablename__ = "mock_items"

    name: Mapped[str] = mapped_column(String(50), nullable=False)


class TestBackendInitialization(unittest.TestCase):
    """Test suite for backend configuration, database baseline, and FastAPI initialization."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_settings_defaults_and_validation(self) -> None:
        """Verify default settings, computed DB URLs, and CORS parser."""
        settings = Settings(
            ENVIRONMENT="test",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_SERVER="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="test_db",
            BACKEND_CORS_ORIGINS=["http://localhost:3000"],
        )
        self.assertEqual(settings.ENVIRONMENT, "test")
        self.assertIsNotNone(settings.DATABASE_URL)
        assert settings.DATABASE_URL is not None
        self.assertIn("postgresql+asyncpg://test_user:test_password@localhost:5432/test_db", settings.DATABASE_URL)
        self.assertIsNotNone(settings.SYNC_DATABASE_URL)
        assert settings.SYNC_DATABASE_URL is not None
        self.assertIn("postgresql+psycopg2://test_user:test_password@localhost:5432/test_db", settings.SYNC_DATABASE_URL)
        self.assertIsNotNone(settings.REDIS_URL)
        assert settings.REDIS_URL is not None
        self.assertIn("redis://localhost:6379/0", settings.REDIS_URL)
        self.assertIn("http://localhost:3000", settings.BACKEND_CORS_ORIGINS)

    def test_settings_cors_string_parsing(self) -> None:
        """Verify comma-separated string CORS origins are parsed into a list."""
        settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:3000")
        self.assertIsInstance(settings.BACKEND_CORS_ORIGINS, list)
        self.assertEqual(len(settings.BACKEND_CORS_ORIGINS), 2)
        self.assertIn("http://localhost:3000", settings.BACKEND_CORS_ORIGINS)
        self.assertIn("http://127.0.0.1:3000", settings.BACKEND_CORS_ORIGINS)

    def test_logging_setup(self) -> None:
        """Verify logging configuration functions without raising exceptions."""
        setup_logging("DEBUG")
        logger = get_logger("unit_test")
        self.assertEqual(logger.name, "keep.unit_test")

    def test_database_base_mixins(self) -> None:
        """Verify Base metadata and column mappings with mixins."""
        table = MockItem.__table__
        self.assertIn("id", table.columns)
        self.assertIn("created_at", table.columns)
        self.assertIn("updated_at", table.columns)
        self.assertIn("name", table.columns)

    def test_root_endpoint(self) -> None:
        """Verify GET / returns service information and online status."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("version", data)
        self.assertIn("name", data)

    def test_health_check_endpoint(self) -> None:
        """Verify GET /api/v1/health returns healthy status."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("environment", data)
        self.assertIn("version", data)
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()

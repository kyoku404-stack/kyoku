"""Root Pytest Configuration and Test Fixtures.

Provides reusable fixtures for backend testing including test settings,
lifespan-managed test clients, and isolated environment variables.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Ensure test environment is configured before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test_super_secret_keep_key_for_testing_purposes_only"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "keep_user"
os.environ["POSTGRES_PASSWORD"] = "keep_password"
os.environ["POSTGRES_DB"] = "keep_test_db"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"

from backend.app.core.config import Settings, settings
from backend.app.main import app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Fixture providing central application settings."""
    return settings


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Fixture providing FastAPI test client with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client

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

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./test.db"

# Register SQLite dialect fallbacks for PostgreSQL types (JSONB, Vector)
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

from backend.app.core.config import Settings, settings
from backend.app.main import app
from backend.app.db.base import Base
from sqlalchemy import create_engine

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"


# Ensure tables are created for integration tests using the app's global engine
sync_test_engine = create_engine("sqlite:///./test.db")
Base.metadata.drop_all(bind=sync_test_engine)
Base.metadata.create_all(bind=sync_test_engine)

# Seed admin user for test clients
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.core.security import get_password_hash

with Session(sync_test_engine) as db_session:
    if not db_session.query(Organization).first():
        org = Organization(name="Enterprise", domain="enterprise.com")
        db_session.add(org)
        db_session.commit()
        user = User(
            email="admin@enterprise.com", 
            hashed_password=get_password_hash("SecurePassword123!"), 
            full_name="Admin User", 
            organization_id=org.id,
            role="OrgAdmin"
        )
        user2 = User(
            email="user@enterprise.com", 
            hashed_password=get_password_hash("SecurePassword123!"), 
            full_name="Standard User", 
            organization_id=org.id,
            role="Member"
        )
        db_session.add(user)
        db_session.add(user2)
        db_session.commit()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Fixture providing central application settings."""
    return settings


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Fixture providing FastAPI test client with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


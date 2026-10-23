"""Application Core Configuration.

Loads environment variables, validates settings, and exposes centralized
configuration parameters using Pydantic v2 BaseSettings.
"""

import json

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings class."""

    # Project Metadata
    PROJECT_NAME: str = "KEEP — Knowledge Extraction & Enterprise Platform"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # Server Network Binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Security & Cryptography
    SECRET_KEY: str = "super_secret_keep_key_replace_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS Origins
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) if not isinstance(i, str) else i for i in v]
        return []

    # PostgreSQL Relational Persistence
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "keep_user"
    POSTGRES_PASSWORD: str = "keep_password"
    POSTGRES_DB: str = "keep_db"

    DATABASE_URL: str | None = None
    SYNC_DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "keep_user")
        password = data.get("POSTGRES_PASSWORD", "keep_password")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "keep_db")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_connection(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "keep_user")
        password = data.get("POSTGRES_PASSWORD", "keep_password")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "keep_db")
        return f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"

    # Redis Cache & Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_URL: str | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        host = data.get("REDIS_HOST", "localhost")
        port = data.get("REDIS_PORT", 6379)
        password = data.get("REDIS_PASSWORD", "")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{host}:{port}/0"

    # Local Storage & Document System
    UPLOAD_STORAGE_PATH: str = "./uploads"
    STORAGE_ROOT: str = "./storage"
    DEFAULT_STORAGE_QUOTA_BYTES: int = (
        10 * 1024 * 1024 * 1024
    )  # 10 GB default quota per org

    # Production Database Connection Pooling & Sizing (Phase 1.10)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True
    DB_STATEMENT_TIMEOUT_MS: int = 30000

    # Production Server Performance & Security (Phase 1.10)
    ENABLE_OPENAPI_DOCS: bool = True
    GZIP_MINIMUM_SIZE: int = 1000
    ENFORCE_SSL_REDIRECT: bool = False
    UVICORN_WORKERS: int = 4
    GRACEFUL_SHUTDOWN_TIMEOUT_SEC: int = 15

    @property
    def is_production(self) -> bool:
        """Determines if the application is running in production mode."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_staging(self) -> bool:
        """Determines if the application is running in staging mode."""
        return self.ENVIRONMENT.lower() == "staging"

    @property
    def is_development(self) -> bool:
        """Determines if the application is running in local development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    @property
    def is_testing(self) -> bool:
        """Determines if the application is running under test execution."""
        return self.ENVIRONMENT.lower() in ("testing", "test")

    def validate_production_configuration(self) -> list[str]:
        """Validates production readiness and emits security alerts or warnings."""
        warnings: list[str] = []
        if self.is_production:
            if self.SECRET_KEY == "super_secret_keep_key_replace_in_production_2026":
                warnings.append(
                    "CRITICAL: Default development SECRET_KEY detected in production environment."
                )
            if len(self.SECRET_KEY) < 32:
                warnings.append(
                    "CRITICAL: SECRET_KEY is too short for production (must be >= 32 characters)."
                )
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                warnings.append(
                    "WARNING: Production DATABASE_URL appears to reference local loopback interface."
                )
        return warnings

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", ".env.development"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()


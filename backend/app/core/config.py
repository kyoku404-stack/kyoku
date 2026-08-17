from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "KEEP — Knowledge Extraction & Enterprise Platform"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"
    
    # Security & Auth
    SECRET_KEY: str = "super_secret_keep_key_replace_in_production_2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "keep_user"
    POSTGRES_PASSWORD: str = "keep_password"
    POSTGRES_DB: str = "keep_db"
    DATABASE_URL: str = "postgresql+asyncpg://keep_user:keep_password@localhost:5432/keep_db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

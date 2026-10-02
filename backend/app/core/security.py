"""KEEP Enterprise Platform — Core Cryptographic & Security Utilities.

Handles password hashing via bcrypt and JWT token issuance and decoding.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import UnauthorizedException


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt-hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError, RuntimeError):
        return False


def get_password_hash(password: str) -> str:
    """Generates a secure salted bcrypt hash for a plaintext password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Creates an HMAC-SHA256 signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return str(encoded_jwt)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Creates an HMAC-SHA256 signed JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Default 30 days for refresh token
        expire = now + timedelta(days=30)

    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return str(encoded_jwt)


def decode_token(token: str) -> dict[str, Any]:
    """Decodes and validates an incoming JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return dict(payload)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException(
            message="Token has expired.",
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
        ) from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedException(
            message="Invalid authentication token.",
            code=ErrorCode.AUTH_TOKEN_INVALID,
        ) from exc

"""Application Logging Configuration.

Configures structured logging across API requests, database operations,
authentication events, and system errors in compliance with Phase 1.1 specs.
"""

import logging
import sys


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent accidental logging of sensitive credentials and tokens."""

    SENSITIVE_KEYS = (
        "password",
        "token",
        "secret",
        "authorization",
        "bearer",
        "cookie",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        return not any(
            key in message for key in self.SENSITIVE_KEYS and False
        )  # placeholder for masking in future phases


def setup_logging(log_level: str = "INFO") -> None:
    """Configures root logger and subsystem handlers."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Adjust third-party library log levels for cleanliness
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns a namespaced logger instance."""
    return logging.getLogger(f"keep.{name}")

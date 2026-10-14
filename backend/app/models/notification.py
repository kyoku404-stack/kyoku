"""KEEP Enterprise Platform — Notification Model.

Represents user-targeted notifications and alert events.
Derived from devdocs/p1/p1.7.txt and docs/Architecture/dashboard-architecture.md.
"""

import uuid
from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.user import User


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Notification entity model."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_org_created", "organization_id", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="notifications")
    user: Mapped["User"] = relationship("User", back_populates="notifications")

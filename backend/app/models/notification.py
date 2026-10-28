"""KEEP Enterprise Platform — Notification Model.

Represents user-targeted notifications and alert events.
Derived from devdocs/p1/p1.7.txt and docs/Architecture/dashboard-architecture.md.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.user import User


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Notification entity model supporting Phase 1.7 in-app alerts and Phase 3.4 multi-channel automation."""

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

    # Phase 3.4 enhancements
    channel: Mapped[str] = mapped_column(String(30), default="IN_APP", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="WORKFLOW", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="notifications")
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    @property
    def message(self) -> str:
        return self.body

    @message.setter
    def message(self, value: str) -> None:
        self.body = value

    @property
    def link_url(self) -> str | None:
        return self.action_url

    @link_url.setter
    def link_url(self, value: str | None) -> None:
        self.action_url = value


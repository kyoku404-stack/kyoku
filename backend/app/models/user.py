"""KEEP Enterprise Platform — User Model.

Represents enterprise credentials, profile information, and role assignments.
"""

import uuid
from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.activity import ActivityLog
    from backend.app.models.chat import ChatSession
    from backend.app.models.department import Department
    from backend.app.models.document import Document
    from backend.app.models.meeting import Meeting
    from backend.app.models.organization import Organization
    from backend.app.models.project import Project
    from backend.app.models.team import Team


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User entity model."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="Member", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    team: Mapped["Team | None"] = relationship(
        "Team",
        back_populates="users",
        foreign_keys=[team_id],
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="users",
        foreign_keys=[department_id],
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        secondary="project_users",
        back_populates="users",
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="uploader")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    meetings: Mapped[list["Meeting"]] = relationship("Meeting", back_populates="organizer")

"""KEEP Enterprise Platform — Project Model.

Represents goal-bound, collaborative workspace initiatives.
"""

import uuid
from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.document import Document
    from backend.app.models.meeting import Meeting
    from backend.app.models.organization import Organization
    from backend.app.models.task import Task
    from backend.app.models.team import Team
    from backend.app.models.user import User

project_users = Table(
    "project_users",
    Base.metadata,
    Column(
        "project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Project entity model."""

    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), index=True, nullable=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)
    timeline: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    team: Mapped["Team | None"] = relationship("Team", back_populates="projects")
    owner: Mapped["User | None"] = relationship("User", foreign_keys=[owner_id])
    users: Mapped[list["User"]] = relationship("User", secondary=project_users, back_populates="projects")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="project")
    meetings: Mapped[list["Meeting"]] = relationship("Meeting", back_populates="project")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")

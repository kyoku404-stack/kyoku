"""KEEP Enterprise Platform — Organization Model.

Root multi-tenant container for enterprise isolation.
"""

from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.activity import ActivityLog
    from backend.app.models.department import Department
    from backend.app.models.document import Document
    from backend.app.models.invitation import Invitation
    from backend.app.models.knowledge import KgEntity, KgRelationship
    from backend.app.models.project import Project
    from backend.app.models.team import Team
    from backend.app.models.user import User


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Organization / Tenant entity model."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    subscription: Mapped[str | None] = mapped_column(String(50), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    time_zone: Mapped[str | None] = mapped_column(String(100), default="UTC", nullable=True)
    default_language: Mapped[str | None] = mapped_column(String(20), default="en-US", nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department", back_populates="organization", cascade="all, delete-orphan"
    )
    teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="organization", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="organization", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="organization", cascade="all, delete-orphan"
    )
    kg_entities: Mapped[list["KgEntity"]] = relationship(
        "KgEntity", back_populates="organization", cascade="all, delete-orphan"
    )
    kg_relationships: Mapped[list["KgRelationship"]] = relationship(
        "KgRelationship", back_populates="organization", cascade="all, delete-orphan"
    )

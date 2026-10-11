"""KEEP Enterprise Platform — Team Model.

Represents operational collaborative units within a department and organization.
"""

import uuid
from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.department import Department
    from backend.app.models.organization import Organization
    from backend.app.models.project import Project
    from backend.app.models.user import User


class Team(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Team entity model."""

    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_teams_org_name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    lead_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="teams")
    department: Mapped["Department | None"] = relationship("Department", back_populates="teams")
    lead: Mapped["User | None"] = relationship("User", foreign_keys=[lead_user_id])
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="team",
        foreign_keys="User.team_id",
    )
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="team")

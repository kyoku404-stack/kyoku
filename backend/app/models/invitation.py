"""KEEP Enterprise Platform — User Invitation Model.

Tracks pending, accepted, and revoked enterprise member invitations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.department import Department
    from backend.app.models.organization import Organization
    from backend.app.models.team import Team
    from backend.app.models.user import User


class Invitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Member invitation model."""

    __tablename__ = "invitations"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", "status", name="uq_invitations_org_email_pending"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="Member", nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="invitations",
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        foreign_keys=[department_id],
    )
    team: Mapped["Team | None"] = relationship(
        "Team",
        foreign_keys=[team_id],
    )
    invited_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )

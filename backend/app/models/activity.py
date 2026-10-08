import uuid

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ActivityLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "activity_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    details: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    organization = relationship("Organization", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")

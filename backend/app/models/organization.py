from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    subscription: Mapped[str | None] = mapped_column(String(50), nullable=True)

    users = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    teams = relationship(
        "Team", back_populates="organization", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="organization", cascade="all, delete-orphan"
    )
    activity_logs = relationship(
        "ActivityLog", back_populates="organization", cascade="all, delete-orphan"
    )
    kg_entities = relationship(
        "KgEntity", back_populates="organization", cascade="all, delete-orphan"
    )
    kg_relationships = relationship(
        "KgRelationship", back_populates="organization", cascade="all, delete-orphan"
    )

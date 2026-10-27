import uuid

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )

    document = relationship("Document", back_populates="chunks")
    document_version = relationship("DocumentVersion", back_populates="chunks")


class KgEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "kg_entities"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    properties_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )

    organization = relationship("Organization", back_populates="kg_entities")
    outgoing_relationships = relationship(
        "KgRelationship",
        foreign_keys="KgRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "KgRelationship",
        foreign_keys="KgRelationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan",
    )


class KgRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "kg_relationships"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    properties_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )

    organization = relationship("Organization", back_populates="kg_relationships")
    source_entity = relationship("KgEntity", foreign_keys=[source_entity_id], back_populates="outgoing_relationships")
    target_entity = relationship("KgEntity", foreign_keys=[target_entity_id], back_populates="incoming_relationships")

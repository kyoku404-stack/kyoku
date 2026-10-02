import uuid
from sqlalchemy import String, ForeignKey, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, server_default='{}', nullable=True)

    document = relationship("Document", back_populates="chunks")

class KgEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "kg_entities"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    properties_json: Mapped[dict | None] = mapped_column(JSONB, server_default='{}', nullable=True)

    organization = relationship("Organization", back_populates="kg_entities")

class KgRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "kg_relationships"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    organization = relationship("Organization", back_populates="kg_relationships")

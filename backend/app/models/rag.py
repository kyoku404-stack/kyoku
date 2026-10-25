import uuid

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RAGQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Logs enterprise RAG query interactions, retrieval counts, tokens, and latency."""

    __tablename__ = "rag_queries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_grounded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dense_candidates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sparse_candidates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reranked_chunks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    generation_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    citations_json: Mapped[list | dict | None] = mapped_column(
        JSONB, server_default="[]", nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )

    organization = relationship("Organization")
    user = relationship("User")
    session = relationship("ChatSession")
    feedbacks = relationship("RAGFeedback", back_populates="query", cascade="all, delete-orphan")


class RAGFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores user satisfaction evaluations, star ratings, and comments for RAG queries."""

    __tablename__ = "rag_feedbacks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rag_queries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_helpful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization")
    user = relationship("User")
    query = relationship("RAGQuery", back_populates="feedbacks")

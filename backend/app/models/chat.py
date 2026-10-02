import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

class ChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    citations_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    session = relationship("ChatSession", back_populates="messages")

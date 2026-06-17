"""
Conversation and Message models.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    HUMAN_AGENT = "human_agent"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    WAITING = "waiting"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus), default=ConversationStatus.ACTIVE
    )
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assigned_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_provider_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(SAEnum(MessageType), default=MessageType.TEXT)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    platform_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    intent_detected: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

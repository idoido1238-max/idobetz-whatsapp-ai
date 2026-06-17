"""
User model - stores customer profile, preferences, and loyalty data.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Integer, Float, DateTime, Text, JSON,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class Platform(str, enum.Enum):
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"
    WEBSITE = "website"


class UserTier(str, enum.Enum):
    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    VIP = "vip"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform), nullable=False)
    platform_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(10), default="he")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    tier: Mapped[UserTier] = mapped_column(SAEnum(UserTier), default=UserTier.STANDARD)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0)
    total_purchases: Mapped[float] = mapped_column(Float, default=0.0)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    birthday: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    opt_in_marketing: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    loyalty_transactions: Mapped[List["LoyaltyTransaction"]] = relationship(
        "LoyaltyTransaction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.platform}:{self.platform_id}>"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    preferred_categories: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    wishlist: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    purchase_history_summary: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    behavioral_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    churn_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    satisfaction_score: Mapped[float] = mapped_column(Float, default=0.0)
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    referred_by: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ai_persona_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50))  # earn | redeem | expire | bonus
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="loyalty_transactions")

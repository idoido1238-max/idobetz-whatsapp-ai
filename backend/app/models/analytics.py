"""
Analytics and A/B Testing models.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    properties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ABTest(Base):
    __tablename__ = "ab_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    traffic_split: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"A": 50, "B": 50}
    metric: Mapped[str] = mapped_column(String(100), default="conversion")
    winner_variant: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variants: Mapped[list] = relationship("ABTestVariant", back_populates="test", cascade="all, delete-orphan")


class ABTestVariant(Base):
    __tablename__ = "ab_test_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ab_tests.id"))
    variant_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_sum: Mapped[float] = mapped_column(Float, default=0.0)

    test: Mapped["ABTest"] = relationship("ABTest", back_populates="variants")

    @property
    def conversion_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions

    @property
    def avg_satisfaction(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.satisfaction_sum / self.impressions

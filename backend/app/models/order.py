"""
Order and OrderItem models - pulled from website API.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    external_order_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="ILS")

    # Shipping address - full display
    shipping_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_street: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shipping_city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    shipping_country: Mapped[str] = mapped_column(String(100), default="Israel")
    shipping_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def full_address(self) -> str:
        """Return full shipping address as formatted string."""
        parts = []
        if self.shipping_street:
            parts.append(self.shipping_street)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_postal_code:
            parts.append(self.shipping_postal_code)
        if self.shipping_country:
            parts.append(self.shipping_country)
        return ", ".join(filter(None, parts))


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    product_image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="items")

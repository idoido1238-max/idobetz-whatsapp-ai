"""
Product model - populated entirely from website API integration.
No hardcoded product data. All data comes from external API sync.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_he: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")
    subcategories: Mapped[List["ProductCategory"]] = relationship("ProductCategory")


class Product(Base):
    """
    Product data - populated exclusively from website API.
    No hardcoded product names or data.
    """
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_he: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_he: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sale_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="ILS")
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory", back_populates="products")
    media: Mapped[List["ProductMedia"]] = relationship(
        "ProductMedia", back_populates="product", cascade="all, delete-orphan"
    )

    @property
    def effective_price(self) -> float:
        return self.sale_price if self.sale_price else self.price

    @property
    def is_on_sale(self) -> bool:
        return self.sale_price is not None and self.sale_price < self.price


class ProductMedia(Base):
    __tablename__ = "product_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="image")  # image | video | pdf
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="media")

"""
Products router - manage product data from website API.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.product import Product, ProductCategory
from app.services.website.product_sync import ProductSyncService

router = APIRouter()
product_sync = ProductSyncService()


@router.get("")
async def list_products(
    category_id: Optional[str] = None,
    in_stock: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List products from website API cache."""
    query = select(Product).where(Product.is_active == True)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if in_stock is not None:
        query = query.where(Product.in_stock == in_stock)
    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%") | Product.name_he.ilike(f"%{search}%")
        )
    query = query.order_by(desc(Product.updated_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    products = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "external_id": p.external_id,
            "sku": p.sku,
            "name": p.name,
            "name_he": p.name_he,
            "price": p.price,
            "sale_price": p.sale_price,
            "effective_price": p.effective_price,
            "is_on_sale": p.is_on_sale,
            "currency": p.currency,
            "in_stock": p.in_stock,
            "stock_quantity": p.stock_quantity,
            "is_featured": p.is_featured,
            "thumbnail_url": p.thumbnail_url,
            "url": p.url,
            "tags": p.tags,
            "synced_at": p.synced_at.isoformat() if p.synced_at else None,
        }
        for p in products
    ]


@router.post("/sync")
async def trigger_sync(_: dict = Depends(get_admin_user)):
    """Manually trigger product sync from website API."""
    import asyncio
    asyncio.create_task(product_sync.sync_all())
    return {"message": "Product sync triggered"}


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List product categories."""
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.is_active == True)
    )
    categories = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "external_id": c.external_id,
            "name": c.name,
            "name_he": c.name_he,
            "slug": c.slug,
        }
        for c in categories
    ]

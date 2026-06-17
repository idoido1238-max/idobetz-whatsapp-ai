"""
Orders router.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.order import Order, OrderStatus

router = APIRouter()


@router.get("")
async def list_orders(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List orders."""
    query = select(Order).order_by(desc(Order.created_at))
    if status:
        try:
            query = query.where(Order.status == OrderStatus(status))
        except ValueError:
            pass
    if user_id:
        query = query.where(Order.user_id == user_id)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": str(o.id),
            "external_order_id": o.external_order_id,
            "status": o.status,
            "total_amount": o.total_amount,
            "currency": o.currency,
            "shipping_city": o.shipping_city,
            "full_address": o.full_address,
            "tracking_number": o.tracking_number,
            "carrier": o.carrier,
            "estimated_delivery": o.estimated_delivery.isoformat() if o.estimated_delivery else None,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get order details."""
    result = await db.execute(
        select(Order).where(Order.external_order_id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": str(order.id),
        "external_order_id": order.external_order_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "shipping_name": order.shipping_name,
        "shipping_street": order.shipping_street,
        "shipping_city": order.shipping_city,
        "shipping_state": order.shipping_state,
        "shipping_postal_code": order.shipping_postal_code,
        "shipping_country": order.shipping_country,
        "full_address": order.full_address,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        "created_at": order.created_at.isoformat(),
    }

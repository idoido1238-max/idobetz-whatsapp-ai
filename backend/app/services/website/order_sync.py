"""
Order sync service - pulls orders from website API in real-time.
Enables smart order tracking with full address display.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class OrderSyncService:
    """
    Syncs orders from website API.
    Enables AI to provide detailed order status with full shipping address.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.api_url = settings.WEBSITE_API_URL
        self.api_key = settings.WEBSITE_API_KEY
        self.headers = {
            "Authorization": f"******",
            "Content-Type": "application/json",
        }

    async def start_scheduler(self):
        if not self.api_url:
            return
        self.scheduler.add_job(
            self.sync_recent_orders,
            "interval",
            minutes=settings.ORDER_SYNC_INTERVAL_MINUTES,
            id="order_sync",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info(f"Order sync scheduler started (every {settings.ORDER_SYNC_INTERVAL_MINUTES} minutes)")

    async def stop_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def sync_recent_orders(self):
        """Sync recent orders from website API."""
        if not self.api_url:
            return
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/orders",
                    headers=self.headers,
                    params={"status": "any", "per_page": 50, "orderby": "date", "order": "desc"},
                )
                response.raise_for_status()
                orders_data = response.json()

            orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])

            async with AsyncSessionLocal() as session:
                for order_data in orders:
                    await self._upsert_order(session, order_data)
                await session.commit()

            logger.info(f"Synced {len(orders)} orders")
        except Exception as e:
            logger.error(f"Order sync error: {e}")

    async def get_order_by_id(self, external_order_id: str) -> Optional[Order]:
        """Get order by external ID."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order).where(Order.external_order_id == external_order_id)
            )
            return result.scalar_one_or_none()

    async def get_user_orders(self, user_id: str, limit: int = 5) -> List[Order]:
        """Get recent orders for a user."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    def format_order_for_message(self, order: Order) -> str:
        """
        Format order info for a WhatsApp/messenger message with full address.
        Example: "אני רואה את ההזמנה שלך #12345 בדרך לתל אביב, רחוב הרצל 5..."
        """
        status_map = {
            OrderStatus.PENDING: "ממתין לאישור",
            OrderStatus.CONFIRMED: "אושר",
            OrderStatus.PROCESSING: "בהכנה",
            OrderStatus.SHIPPED: "נשלח",
            OrderStatus.OUT_FOR_DELIVERY: "בדרך אליך",
            OrderStatus.DELIVERED: "נמסר",
            OrderStatus.CANCELLED: "בוטל",
            OrderStatus.REFUNDED: "הוחזר",
        }
        status_he = status_map.get(order.status, order.status)

        lines = [f"📦 הזמנה #{order.external_order_id}"]
        lines.append(f"סטטוס: {status_he}")

        if order.shipping_city:
            address_parts = []
            if order.shipping_street:
                address_parts.append(order.shipping_street)
            address_parts.append(order.shipping_city)
            if order.shipping_postal_code:
                address_parts.append(order.shipping_postal_code)
            lines.append(f"כתובת משלוח: {', '.join(address_parts)}")

        if order.tracking_number:
            lines.append(f"מספר מעקב: {order.tracking_number}")
            if order.carrier:
                lines.append(f"חברת שילוח: {order.carrier}")

        if order.estimated_delivery:
            lines.append(f"זמן אספקה משוער: {order.estimated_delivery.strftime('%d/%m/%Y')}")

        lines.append(f"סכום: {order.total_amount:.2f} ₪")
        return "\n".join(lines)

    async def _upsert_order(self, session, order_data: Dict[str, Any]):
        """Insert or update an order from API data."""
        external_id = str(order_data.get("id", ""))
        result = await session.execute(
            select(Order).where(Order.external_order_id == external_id)
        )
        order = result.scalar_one_or_none()

        # Map status
        status_map = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.PROCESSING,
            "on-hold": OrderStatus.CONFIRMED,
            "completed": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED,
            "refunded": OrderStatus.REFUNDED,
            "failed": OrderStatus.CANCELLED,
            "shipped": OrderStatus.SHIPPED,
        }
        raw_status = order_data.get("status", "pending").lower()
        order_status = status_map.get(raw_status, OrderStatus.PENDING)

        # Extract shipping from various API formats
        shipping = order_data.get("shipping", order_data.get("shipping_address", {}))

        order_dict = {
            "status": order_status,
            "total_amount": float(order_data.get("total", 0)),
            "currency": order_data.get("currency", "ILS"),
            "shipping_name": shipping.get("name", f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip()),
            "shipping_street": shipping.get("address_1", shipping.get("street")),
            "shipping_city": shipping.get("city"),
            "shipping_state": shipping.get("state"),
            "shipping_postal_code": shipping.get("postcode", shipping.get("postal_code")),
            "shipping_country": shipping.get("country", "IL"),
            "shipping_phone": shipping.get("phone"),
            "tracking_number": order_data.get("tracking_number"),
            "carrier": order_data.get("shipping_lines", [{}])[0].get("method_title") if order_data.get("shipping_lines") else None,
        }

        if order:
            for key, value in order_dict.items():
                setattr(order, key, value)
        else:
            order = Order(external_order_id=external_id, **order_dict)
            session.add(order)

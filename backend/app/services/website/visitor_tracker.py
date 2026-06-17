"""
Website visitor tracking (privacy compliant).
Handles abandoned cart detection and visitor identification.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from app.redis_client import RedisCache

logger = logging.getLogger(__name__)

visitor_cache = RedisCache(prefix="visitor")


class VisitorTracker:
    """
    Privacy-compliant visitor tracking.
    Stores session data in Redis with TTL.
    No PII stored without user consent.
    """

    CART_ABANDONMENT_THRESHOLD_MINUTES = 30

    async def track_page_view(self, session_id: str, page: str, metadata: Optional[Dict] = None):
        """Track a page view."""
        event = {
            "type": "page_view",
            "page": page,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        await self._append_event(session_id, event)

    async def track_cart_event(self, session_id: str, event_type: str, cart_data: Dict[str, Any]):
        """
        Track cart add/remove/update events.
        cart_data should contain generic product info only (no hardcoded products).
        """
        event = {
            "type": f"cart_{event_type}",
            "cart_value": cart_data.get("total", 0),
            "item_count": cart_data.get("item_count", 0),
            "category": cart_data.get("category"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._append_event(session_id, event)
        await visitor_cache.set(f"cart:{session_id}", cart_data, ttl=86400)

    async def get_abandoned_cart(self, session_id: str) -> Optional[Dict]:
        """Check if cart was abandoned."""
        cart_data = await visitor_cache.get(f"cart:{session_id}")
        if not cart_data:
            return None

        last_activity = await visitor_cache.get(f"last_activity:{session_id}")
        if not last_activity:
            return None

        last_time = datetime.fromisoformat(last_activity)
        threshold = datetime.utcnow() - timedelta(minutes=self.CART_ABANDONMENT_THRESHOLD_MINUTES)
        if last_time < threshold and cart_data.get("total", 0) > 0:
            return cart_data
        return None

    async def link_visitor_to_user(self, session_id: str, user_id: str):
        """Link anonymous visitor session to authenticated user."""
        await visitor_cache.set(f"user_link:{session_id}", user_id, ttl=86400 * 7)
        logger.info(f"Visitor {session_id} linked to user {user_id}")

    async def _append_event(self, session_id: str, event: Dict):
        """Append event to visitor session."""
        client_key = f"events:{session_id}"
        events = await visitor_cache.get(client_key) or []
        events.append(event)
        # Keep last 50 events
        if len(events) > 50:
            events = events[-50:]
        await visitor_cache.set(client_key, events, ttl=86400)
        await visitor_cache.set(
            f"last_activity:{session_id}",
            datetime.utcnow().isoformat(),
            ttl=86400,
        )

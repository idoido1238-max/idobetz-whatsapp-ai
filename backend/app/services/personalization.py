"""
Personalization service.
Builds user context and personalizes AI responses based on user history.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User, UserProfile, UserTier
from app.models.order import Order, OrderStatus
from app.redis_client import user_cache

logger = logging.getLogger(__name__)


class PersonalizationService:
    """
    Provides personalized context and messages for each user.
    """

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Build complete user context for AI personalization.
        Returns cached context or builds fresh.
        """
        cache_key = f"context:{user_id}"
        cached = await user_cache.get(cache_key)
        if cached:
            return cached

        context = await self._build_user_context(user_id)
        await user_cache.set(cache_key, context, ttl=300)
        return context

    async def _build_user_context(self, user_id: str) -> Dict[str, Any]:
        """Build user context from database."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return {}

            # Get recent orders
            orders_result = await session.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(5)
            )
            recent_orders = list(orders_result.scalars().all())

        context = {
            "user_id": str(user.id),
            "name": user.name or "חבר/ה יקר/ה",
            "tier": user.tier.value,
            "is_vip": user.tier in (UserTier.VIP, UserTier.PLATINUM),
            "loyalty_points": user.loyalty_points,
            "language": user.language,
            "total_purchases": user.total_purchases,
            "purchase_count": user.purchase_count,
            "is_birthday": self._is_birthday(user.birthday),
            "recent_orders": [
                {
                    "id": order.external_order_id,
                    "status": order.status.value,
                    "amount": order.total_amount,
                    "city": order.shipping_city,
                    "address": order.full_address,
                }
                for order in recent_orders
            ],
            "is_new_customer": user.purchase_count == 0,
            "is_returning": user.purchase_count > 0,
            "days_since_last_purchase": self._days_since(
                recent_orders[0].created_at if recent_orders else None
            ),
        }

        if user.profile:
            context.update({
                "preferred_categories": user.profile.preferred_categories,
                "wishlist": user.profile.wishlist,
                "churn_risk": user.profile.churn_risk_score,
                "satisfaction": user.profile.satisfaction_score,
            })

        return context

    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build personalized system prompt for AI based on user context."""
        name = context.get("name", "")
        tier = context.get("tier", "standard")
        is_vip = context.get("is_vip", False)
        loyalty_points = context.get("loyalty_points", 0)
        is_birthday = context.get("is_birthday", False)
        is_new = context.get("is_new_customer", True)

        prompt_parts = [
            "אתה עוזר חכם ומועיל של idobetz. ענה בעברית תמיד.",
            f"שם הלקוח: {name}",
        ]

        if is_vip:
            prompt_parts.append("זהו לקוח VIP - תן שירות מועדף ומהיר.")
        elif tier == "gold":
            prompt_parts.append("זהו לקוח זהב - תן שירות מצוין.")

        if is_birthday:
            prompt_parts.append("🎂 היום יום ההולדת של הלקוח! ברך אותו בחום!")

        if is_new:
            prompt_parts.append("זהו לקוח חדש - הסבר בסבלנות ועזור לו להתמצא.")
        else:
            prompt_parts.append(f"הלקוח ביצע {context.get('purchase_count', 0)} הזמנות בעבר.")

        if loyalty_points > 0:
            prompt_parts.append(f"יש ללקוח {loyalty_points} נקודות נאמנות.")

        recent_orders = context.get("recent_orders", [])
        if recent_orders:
            latest = recent_orders[0]
            if latest.get("city"):
                prompt_parts.append(
                    f"ההזמנה האחרונה שלו: #{latest['id']} - {latest['status']} - "
                    f"בדרך ל{latest['city']}."
                )

        prompt_parts.extend([
            "היה ידידותי, קצר ולענין.",
            "אם יש מידע על הזמנה - ספר את זה בצורה אישית.",
            "אל תמציא פרטים על מוצרים שלא ניתנו לך.",
        ])

        return "\n".join(prompt_parts)

    def _is_birthday(self, birthday: Optional[datetime]) -> bool:
        if not birthday:
            return False
        today = datetime.utcnow()
        return birthday.month == today.month and birthday.day == today.day

    def _days_since(self, dt: Optional[datetime]) -> Optional[int]:
        if not dt:
            return None
        return (datetime.utcnow() - dt).days

    async def update_behavioral_data(self, user_id: str, event: str, data: Dict):
        """Update user behavioral data based on interaction."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile:
                behavioral = profile.behavioral_data or {}
                event_list = behavioral.get(event, [])
                event_list.append({**data, "timestamp": datetime.utcnow().isoformat()})
                behavioral[event] = event_list[-20:]  # Keep last 20 events
                profile.behavioral_data = behavioral
                await session.commit()

    async def predict_churn_risk(self, user_id: str) -> float:
        """
        Simple churn risk prediction based on activity.
        Returns score 0-1 (1 = high risk).
        """
        context = await self.get_user_context(user_id)
        days_since = context.get("days_since_last_purchase")

        if days_since is None:
            return 0.3  # New user, moderate risk

        if days_since > 90:
            return 0.9
        elif days_since > 60:
            return 0.7
        elif days_since > 30:
            return 0.4
        else:
            return 0.1

    async def get_vip_greeting(self, user_id: str) -> str:
        """Get personalized VIP greeting."""
        context = await self.get_user_context(user_id)
        name = context.get("name", "")
        tier = context.get("tier", "standard")
        is_birthday = context.get("is_birthday", False)

        if is_birthday:
            return f"🎂 יום הולדת שמח {name}! במתנה מאיתנו - 20% הנחה על הזמנה הבאה!"

        tier_greetings = {
            "vip": f"👑 שלום {name}, לקוח VIP יקר! איך אוכל לעזור לך היום?",
            "platinum": f"💎 שלום {name}! תמיד שמח לראות אותך. מה צריך?",
            "gold": f"⭐ שלום {name}! לקוח זהב חשוב. במה אעזור?",
            "silver": f"🥈 שלום {name}! מה שלומך היום?",
        }

        return tier_greetings.get(tier, f"שלום {name}! איך אוכל לעזור?")

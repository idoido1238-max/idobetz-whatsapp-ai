"""
Audit logging service for GDPR compliance and security.
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.database import AsyncSessionLocal
from app.models.analytics import AnalyticsEvent

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    GDPR-compliant audit logging.
    Tracks all data access and modifications.
    """

    async def log(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        platform: Optional[str] = None,
        value: Optional[float] = None,
    ):
        """Log an audit event to database."""
        try:
            async with AsyncSessionLocal() as session:
                event = AnalyticsEvent(
                    event_type=event_type,
                    user_id=user_id,
                    session_id=session_id,
                    platform=platform,
                    properties=properties or {},
                    value=value,
                    created_at=datetime.utcnow(),
                )
                session.add(event)
                await session.commit()
        except Exception as e:
            logger.error(f"Audit log error: {e}")

    async def log_message_received(self, platform: str, user_id: str, session_id: str):
        await self.log("message_received", user_id, session_id, platform=platform)

    async def log_message_sent(self, platform: str, user_id: str, session_id: str, ai_provider: str):
        await self.log(
            "message_sent",
            user_id,
            session_id,
            platform=platform,
            properties={"ai_provider": ai_provider},
        )

    async def log_user_created(self, user_id: str, platform: str):
        await self.log("user_created", user_id, platform=platform)

    async def log_order_viewed(self, user_id: str, order_id: str):
        await self.log("order_viewed", user_id, properties={"order_id": order_id})

    async def log_campaign_sent(self, campaign_id: str, recipient_count: int):
        await self.log(
            "campaign_sent",
            properties={"campaign_id": campaign_id, "recipient_count": recipient_count},
        )

    async def log_data_export(self, user_id: str, exported_by: str):
        """GDPR: log data export requests."""
        await self.log(
            "gdpr_data_export",
            user_id,
            properties={"exported_by": exported_by},
        )

    async def log_data_deletion(self, user_id: str, deleted_by: str):
        """GDPR: log data deletion requests."""
        await self.log(
            "gdpr_data_deletion",
            user_id,
            properties={"deleted_by": deleted_by},
        )


audit_logger = AuditLogger()

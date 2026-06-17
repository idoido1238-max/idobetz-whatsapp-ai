"""
Campaign service - manages broadcast, scheduled, and automated campaigns.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.campaign import Campaign, CampaignRecipient, CampaignStatus, CampaignType
from app.models.user import User, UserTier
from app.services.platforms.whatsapp import WhatsAppHandler

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Manages all campaign types: broadcast, scheduled, abandoned cart,
    birthday, re-engagement, loyalty rewards, and custom campaigns.
    """

    def __init__(self):
        self.whatsapp = WhatsAppHandler()

    async def create_campaign(
        self,
        name: str,
        campaign_type: CampaignType,
        message_content: str,
        message_content_he: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        target_segment: Optional[Dict] = None,
        target_platform: str = "whatsapp",
        target_user_tiers: Optional[List[str]] = None,
        template_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Campaign:
        """Create a new campaign (starts in DRAFT status)."""
        async with AsyncSessionLocal() as session:
            campaign = Campaign(
                name=name,
                campaign_type=campaign_type,
                message_content=message_content,
                message_content_he=message_content_he,
                status=CampaignStatus.DRAFT,
                scheduled_at=scheduled_at,
                target_segment=target_segment or {},
                target_user_tiers=target_user_tiers or [],
                target_platform=target_platform,
                created_by=created_by,
            )
            session.add(campaign)
            await session.commit()
            await session.refresh(campaign)
            return campaign

    async def schedule_campaign(self, campaign_id: str, scheduled_at: datetime) -> Campaign:
        """Schedule a campaign for specific time."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            campaign.scheduled_at = scheduled_at
            campaign.status = CampaignStatus.SCHEDULED
            await session.commit()
            await session.refresh(campaign)
            logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")
            return campaign

    async def activate_campaign(self, campaign_id: str) -> Campaign:
        """Manually activate a campaign."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED, CampaignStatus.PAUSED):
                raise ValueError(f"Cannot activate campaign in status: {campaign.status}")

            campaign.status = CampaignStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            await session.commit()
            await session.refresh(campaign)

        # Start sending async
        await self._send_campaign(campaign)
        return campaign

    async def pause_campaign(self, campaign_id: str) -> Campaign:
        """Pause a running campaign."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            campaign.status = CampaignStatus.PAUSED
            await session.commit()
            await session.refresh(campaign)
            logger.info(f"Campaign {campaign_id} paused")
            return campaign

    async def cancel_campaign(self, campaign_id: str) -> Campaign:
        """Cancel a campaign."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if campaign:
                campaign.status = CampaignStatus.CANCELLED
                await session.commit()
                await session.refresh(campaign)
        return campaign

    async def get_target_users(self, campaign: Campaign) -> List[User]:
        """Get target users for a campaign based on segment criteria."""
        async with AsyncSessionLocal() as session:
            query = select(User).where(
                User.is_active == True,
                User.is_blocked == False,
                User.opt_in_marketing == True,
            )

            # Filter by tiers
            if campaign.target_user_tiers:
                tiers = [UserTier(t) for t in campaign.target_user_tiers]
                query = query.where(User.tier.in_(tiers))

            result = await session.execute(query)
            return list(result.scalars().all())

    async def _send_campaign(self, campaign: Campaign):
        """Send campaign messages to all target users."""
        users = await self.get_target_users(campaign)

        async with AsyncSessionLocal() as session:
            campaign_result = await session.execute(
                select(Campaign).where(Campaign.id == campaign.id)
            )
            campaign_db = campaign_result.scalar_one()
            campaign_db.total_recipients = len(users)
            await session.commit()

        sent_count = 0
        for user in users:
            try:
                if campaign.target_platform in ("whatsapp", "all") and user.phone_number:
                    message = campaign.message_content_he or campaign.message_content
                    await self.whatsapp.send_text(user.phone_number, message)

                await self._mark_recipient_sent(str(campaign.id), str(user.id))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send campaign to user {user.id}: {e}")
                await self._mark_recipient_error(str(campaign.id), str(user.id), str(e))

        # Update campaign stats
        async with AsyncSessionLocal() as session:
            campaign_result = await session.execute(
                select(Campaign).where(Campaign.id == campaign.id)
            )
            campaign_db = campaign_result.scalar_one()
            campaign_db.sent_count = sent_count
            campaign_db.status = CampaignStatus.COMPLETED
            campaign_db.completed_at = datetime.utcnow()
            await session.commit()

        logger.info(f"Campaign {campaign.id} completed: {sent_count}/{len(users)} sent")

    async def _mark_recipient_sent(self, campaign_id: str, user_id: str):
        async with AsyncSessionLocal() as session:
            recipient = CampaignRecipient(
                campaign_id=campaign_id,
                user_id=user_id,
                status="sent",
                sent_at=datetime.utcnow(),
            )
            session.add(recipient)
            await session.commit()

    async def _mark_recipient_error(self, campaign_id: str, user_id: str, error: str):
        async with AsyncSessionLocal() as session:
            recipient = CampaignRecipient(
                campaign_id=campaign_id,
                user_id=user_id,
                status="failed",
                error=error,
            )
            session.add(recipient)
            await session.commit()

    async def check_and_send_scheduled(self):
        """Check for scheduled campaigns and send them."""
        now = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Campaign).where(
                    Campaign.status == CampaignStatus.SCHEDULED,
                    Campaign.scheduled_at <= now,
                )
            )
            campaigns = list(result.scalars().all())

        for campaign in campaigns:
            logger.info(f"Triggering scheduled campaign: {campaign.name}")
            await self.activate_campaign(str(campaign.id))

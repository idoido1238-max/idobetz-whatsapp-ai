"""
Campaign management router.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.campaign import Campaign, CampaignType, CampaignStatus
from app.services.campaign_service import CampaignService

router = APIRouter()
campaign_service = CampaignService()


class CreateCampaignRequest(BaseModel):
    name: str
    campaign_type: str
    message_content: str
    message_content_he: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    target_user_tiers: Optional[List[str]] = None
    target_platform: str = "whatsapp"
    description: Optional[str] = None


class ScheduleCampaignRequest(BaseModel):
    scheduled_at: datetime


@router.get("")
async def list_campaigns(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List all campaigns."""
    query = select(Campaign).order_by(desc(Campaign.created_at))
    if status:
        query = query.where(Campaign.status == status)
    result = await db.execute(query)
    campaigns = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "campaign_type": c.campaign_type,
            "status": c.status,
            "target_platform": c.target_platform,
            "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
            "total_recipients": c.total_recipients,
            "sent_count": c.sent_count,
            "delivered_count": c.delivered_count,
            "read_count": c.read_count,
            "conversion_count": c.conversion_count,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


@router.post("")
async def create_campaign(
    request: CreateCampaignRequest,
    current_user: dict = Depends(get_admin_user),
):
    """Create a new campaign."""
    try:
        campaign_type = CampaignType(request.campaign_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid campaign type: {request.campaign_type}")

    campaign = await campaign_service.create_campaign(
        name=request.name,
        campaign_type=campaign_type,
        message_content=request.message_content,
        message_content_he=request.message_content_he,
        scheduled_at=request.scheduled_at,
        target_user_tiers=request.target_user_tiers,
        target_platform=request.target_platform,
        created_by=current_user.get("sub"),
    )

    return {"id": str(campaign.id), "status": campaign.status, "message": "Campaign created successfully"}


@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    _: dict = Depends(get_admin_user),
):
    """Manually activate a campaign immediately."""
    try:
        campaign = await campaign_service.activate_campaign(campaign_id)
        return {"id": str(campaign.id), "status": campaign.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    _: dict = Depends(get_admin_user),
):
    """Pause a running campaign."""
    campaign = await campaign_service.pause_campaign(campaign_id)
    return {"id": str(campaign.id), "status": campaign.status}


@router.post("/{campaign_id}/cancel")
async def cancel_campaign(
    campaign_id: str,
    _: dict = Depends(get_admin_user),
):
    """Cancel a campaign."""
    campaign = await campaign_service.cancel_campaign(campaign_id)
    return {"id": str(campaign.id), "status": campaign.status}


@router.post("/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: str,
    request: ScheduleCampaignRequest,
    _: dict = Depends(get_admin_user),
):
    """Schedule a campaign for a specific time."""
    campaign = await campaign_service.schedule_campaign(campaign_id, request.scheduled_at)
    return {
        "id": str(campaign.id),
        "status": campaign.status,
        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
    }

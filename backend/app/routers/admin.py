"""
Admin router - dashboard data, overview, and management endpoints.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.models.order import Order
from app.models.campaign import Campaign, CampaignStatus, CampaignType, TargetPlatform
from app.models.analytics import AnalyticsEvent
from app.services.ai.router import AIRouter
from app.services.nlp.intent import IntentDetector
from app.services.nlp.sentiment import SentimentAnalyzer
from app.services.nlp.ner import NERService

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instances for chat simulation
_ai_router = AIRouter()
_intent_detector = IntentDetector()
_sentiment_analyzer = SentimentAnalyzer()
_ner_service = NERService()


class SimulateChatRequest(BaseModel):
    message: str
    platform: str = "whatsapp"
    ai_provider: Optional[str] = None
    history: Optional[List[dict]] = None
    user_profile: Optional[str] = "standard"


class AdminCampaignCreateRequest(BaseModel):
    name: str
    campaign_type: str = "broadcast"
    message_content: Optional[str] = None
    message_content_he: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    target_platform: str = "whatsapp"
    target_user_tiers: Optional[List[str]] = None
    target_tags: Optional[List[str]] = None
    target_segment: Optional[dict] = None
    template_id: Optional[str] = None
    status: Optional[str] = None


class AdminCampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    message_content: Optional[str] = None
    message_content_he: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    target_platform: Optional[str] = None
    target_user_tiers: Optional[List[str]] = None
    target_tags: Optional[List[str]] = None
    target_segment: Optional[dict] = None
    template_id: Optional[str] = None
    status: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    is_vip: Optional[bool] = None
    segment: Optional[str] = None


class AdminSettingsUpdateRequest(BaseModel):
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    messenger_token_status: Optional[str] = None
    instagram_business_id: Optional[str] = None
    website_api_url: Optional[str] = None
    bot_name: Optional[str] = None
    response_language: Optional[str] = None
    support_email: Optional[str] = None
    theme: Optional[str] = None


_admin_settings: Dict[str, Optional[str]] = {
    "openai_api_key": "",
    "claude_api_key": "",
    "whatsapp_api_token": "",
    "whatsapp_phone_id": "",
    "messenger_token_status": "not_configured",
    "instagram_business_id": "",
    "website_api_url": "",
    "bot_name": "Idobetz AI",
    "response_language": "he",
    "support_email": "",
    "theme": "light",
}


def _mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


@router.post("/chat/simulate")
async def simulate_chat(
    req: SimulateChatRequest,
    _: dict = Depends(get_admin_user),
):
    """
    Simulate a chat message with the AI bot.
    Returns the AI response along with NLP analysis (intent, sentiment, entities).
    """
    started_at = datetime.utcnow()

    # Build message history for context
    history = req.history or []
    messages = list(history) + [{"role": "user", "content": req.message}]

    system_prompt = (
        "You are a helpful AI customer service assistant for an Israeli e-commerce store. "
        "You support both Hebrew and English. Be friendly, concise, and helpful. "
        "When asked about products, prices, or orders, explain that you would look up "
        "real data from the store system in production. "
        f"Simulated platform: {req.platform}. "
        f"User profile: {req.user_profile}."
    )

    # Run AI, intent, and sentiment in parallel
    ai_task = _ai_router.chat(
        messages=messages,
        system_prompt=system_prompt,
        provider=req.ai_provider,
    )
    intent_task = _intent_detector.detect(req.message, history)
    sentiment_task = _sentiment_analyzer.analyze(req.message)

    try:
        ai_result, intent_result, sentiment_result = await asyncio.gather(
            ai_task, intent_task, sentiment_task, return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        ai_result = {"content": "שגיאה בעיבוד ההודעה. אנא נסה שוב.", "provider": "error"}
        intent_result = {}
        sentiment_result = {}

    # Handle individual task failures gracefully
    if isinstance(ai_result, Exception):
        logger.error(f"AI error: {ai_result}")
        ai_result = {"content": "שגיאה בעיבוד ההודעה. אנא נסה שוב.", "provider": "error", "tokens": 0}
    if isinstance(intent_result, Exception):
        logger.error(f"Intent error: {intent_result}")
        intent_result = {}
    if isinstance(sentiment_result, Exception):
        logger.error(f"Sentiment error: {sentiment_result}")
        sentiment_result = {}

    # NER entities (non-blocking)
    entities = {}
    try:
        entities = await _ner_service.extract_entities(req.message)
    except Exception as e:
        logger.warning(f"NER error: {e}")

    elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    return {
        "response": ai_result.get("content", ""),
        "ai_provider": ai_result.get("provider", req.ai_provider or "openai"),
        "tokens_used": ai_result.get("tokens", 0),
        "response_time_ms": elapsed_ms,
        "intent": intent_result.get("intent"),
        "intent_confidence": intent_result.get("confidence"),
        "entities": intent_result.get("entities", entities),
        "sentiment": sentiment_result.get("sentiment"),
        "sentiment_score": sentiment_result.get("score"),
        "sentiment_emotions": sentiment_result.get("emotions", []),
    }


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Admin dashboard overview stats."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    # Total users
    total_users = await db.scalar(select(func.count(User.id)))

    # New users today
    new_today = await db.scalar(
        select(func.count(User.id)).where(User.first_seen_at >= today_start)
    )

    # Total conversations
    total_convs = await db.scalar(select(func.count(Conversation.id)))

    # Active conversations
    active_convs = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.status == "active",
            Conversation.last_message_at >= now - timedelta(hours=24),
        )
    )

    # Total messages
    total_messages = await db.scalar(select(func.count(Message.id)))

    # Platform breakdown
    platform_stats = await db.execute(
        select(User.platform, func.count(User.id))
        .group_by(User.platform)
    )
    platforms = {str(row[0]): row[1] for row in platform_stats.all()}

    return {
        "total_users": total_users or 0,
        "new_users_today": new_today or 0,
        "total_conversations": total_convs or 0,
        "active_conversations": active_convs or 0,
        "total_messages": total_messages or 0,
        "platform_breakdown": platforms,
        "timestamp": now.isoformat(),
    }


@router.get("/conversations")
async def list_conversations(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List conversations with filters."""
    query = select(Conversation).order_by(desc(Conversation.last_message_at))
    if platform:
        query = query.where(Conversation.platform == platform)
    if status:
        query = query.where(Conversation.status == status)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "platform": c.platform,
            "status": c.status,
            "intent": c.intent,
            "sentiment": c.sentiment,
            "total_messages": c.total_messages,
            "ai_provider": c.ai_provider_used,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get messages for a specific conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "ai_provider": m.ai_provider,
            "tokens_used": m.tokens_used,
            "intent_detected": m.intent_detected,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.get("/campaigns")
async def list_campaigns_admin(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List campaigns with admin filters."""
    query = select(Campaign).order_by(desc(Campaign.created_at))
    if status:
        query = query.where(Campaign.status == status)
    if platform:
        query = query.where(Campaign.target_platform == platform)
    if search:
        query = query.where(Campaign.name.ilike(f"%{search}%"))
    query = query.limit(limit).offset(offset)
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
            "target_user_tiers": c.target_user_tiers or [],
            "target_tags": c.target_tags or [],
            "target_segment": c.target_segment or {},
            "template_id": str(c.template_id) if c.template_id else None,
            "total_recipients": c.total_recipients,
            "sent_count": c.sent_count,
            "read_count": c.read_count,
            "conversion_count": c.conversion_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ]


@router.post("/campaigns")
async def create_campaign_admin(
    request: AdminCampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Create campaign from admin dashboard."""
    try:
        campaign_type = CampaignType(request.campaign_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign type")

    try:
        target_platform = TargetPlatform(request.target_platform)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target platform")

    status = CampaignStatus.DRAFT
    if request.status:
        try:
            status = CampaignStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campaign status")
    elif request.scheduled_at:
        status = CampaignStatus.SCHEDULED

    campaign = Campaign(
        name=request.name,
        campaign_type=campaign_type,
        status=status,
        target_platform=target_platform,
        scheduled_at=request.scheduled_at,
        message_content=request.message_content or request.message_content_he,
        message_content_he=request.message_content_he,
        target_user_tiers=request.target_user_tiers or [],
        target_tags=request.target_tags or [],
        target_segment=request.target_segment or {},
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return {"id": str(campaign.id), "status": campaign.status}


@router.put("/campaigns/{campaign_id}")
async def update_campaign_admin(
    campaign_id: str,
    request: AdminCampaignUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Update campaign fields from admin dashboard."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if request.name is not None:
        campaign.name = request.name
    if request.message_content is not None:
        campaign.message_content = request.message_content
    if request.message_content_he is not None:
        campaign.message_content_he = request.message_content_he
    if request.scheduled_at is not None:
        campaign.scheduled_at = request.scheduled_at
    if request.target_user_tiers is not None:
        campaign.target_user_tiers = request.target_user_tiers
    if request.target_tags is not None:
        campaign.target_tags = request.target_tags
    if request.target_segment is not None:
        campaign.target_segment = request.target_segment
    if request.campaign_type is not None:
        try:
            campaign.campaign_type = CampaignType(request.campaign_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campaign type")
    if request.target_platform is not None:
        try:
            campaign.target_platform = TargetPlatform(request.target_platform)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target platform")
    if request.status is not None:
        try:
            campaign.status = CampaignStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campaign status")

    await db.commit()
    await db.refresh(campaign)
    return {"id": str(campaign.id), "status": campaign.status}


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign_admin(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Delete campaign from admin dashboard."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.delete(campaign)
    await db.commit()
    return {"deleted": True}


@router.get("/users")
async def list_users(
    search: Optional[str] = None,
    platform: Optional[str] = None,
    vip: Optional[bool] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List users with filters."""
    query = select(User).order_by(desc(User.last_seen_at))
    if search:
        like = f"%{search}%"
        query = query.where(or_(User.name.ilike(like), User.email.ilike(like)))
    if platform:
        query = query.where(User.platform == platform)
    if vip is not None:
        if vip:
            query = query.where(User.tier == "vip")
        else:
            query = query.where(User.tier != "vip")
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "platform": u.platform,
            "tier": u.tier,
            "loyalty_points": u.loyalty_points,
            "purchase_count": u.purchase_count,
            "total_purchases": u.total_purchases,
            "is_vip": u.tier == "vip",
            "is_active": u.is_active,
            "join_date": u.first_seen_at.isoformat() if u.first_seen_at else None,
            "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
            "segment": (u.metadata_ or {}).get("segment"),
            "tags": (u.metadata_ or {}).get("tags", []),
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get full user details for admin panel."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders_result = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(desc(Order.created_at)).limit(10)
    )
    orders = orders_result.scalars().all()
    metadata = user.metadata_ or {}
    engagement_score = min(
        100,
        int((user.purchase_count or 0) * 8 + (user.loyalty_points or 0) / 20 + (20 if user.is_active else 0)),
    )

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "platform": user.platform,
        "join_date": user.first_seen_at.isoformat() if user.first_seen_at else None,
        "is_vip": user.tier == "vip",
        "is_active": user.is_active,
        "last_activity": user.last_seen_at.isoformat() if user.last_seen_at else None,
        "segment": metadata.get("segment"),
        "tags": metadata.get("tags", []),
        "lifetime_value": user.total_purchases or 0,
        "engagement_score": engagement_score,
        "purchase_history": [
            {
                "order_id": o.external_order_id,
                "amount": o.total_amount,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
    }


@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: str,
    request: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Update VIP/segment data for user management."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.is_vip is not None:
        user.tier = "vip" if request.is_vip else "standard"

    metadata = user.metadata_ or {}
    if request.segment is not None:
        metadata["segment"] = request.segment
    user.metadata_ = metadata

    await db.commit()
    await db.refresh(user)
    return {"id": str(user.id), "is_vip": user.tier == "vip", "segment": (user.metadata_ or {}).get("segment")}


@router.get("/analytics/overview")
async def get_admin_analytics_overview(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Daily overview metrics for admin analytics."""
    since = datetime.utcnow() - timedelta(days=days)

    dau_result = await db.execute(
        select(func.date(Conversation.started_at), func.count(func.distinct(Conversation.user_id)))
        .where(Conversation.started_at >= since)
        .group_by(func.date(Conversation.started_at))
        .order_by(func.date(Conversation.started_at))
    )
    daily_active_users = [{"date": str(r[0]), "count": r[1]} for r in dau_result.all()]

    avg_response_ms = await db.scalar(
        select(func.avg(Message.processing_time_ms)).where(
            Message.created_at >= since,
            Message.processing_time_ms.isnot(None),
        )
    )
    avg_satisfaction = await db.scalar(
        select(func.avg(Conversation.satisfaction_rating)).where(
            Conversation.started_at >= since,
            Conversation.satisfaction_rating.isnot(None),
        )
    )
    total_orders = await db.scalar(select(func.count(Order.id)).where(Order.created_at >= since))
    converted_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= since, Order.status.in_(["confirmed", "processing", "shipped", "delivered"]))
    )
    revenue = await db.scalar(select(func.sum(Order.total_amount)).where(Order.created_at >= since))
    conversion_rate = ((converted_orders or 0) / (total_orders or 1) * 100) if (total_orders or 0) > 0 else 0
    avg_order_value = (revenue or 0) / (total_orders or 1) if (total_orders or 0) > 0 else 0

    return {
        "daily_active_users": daily_active_users,
        "avg_response_time_ms": round(avg_response_ms or 0, 2),
        "user_satisfaction_score": round(((avg_satisfaction or 0) / 5) * 100, 2),
        "conversion_rate": round(conversion_rate, 2),
        "average_order_value": round(avg_order_value, 2),
    }


@router.get("/analytics/metrics")
async def get_admin_analytics_metrics(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Chart datasets for admin analytics."""
    since = datetime.utcnow() - timedelta(days=days)

    revenue_result = await db.execute(
        select(func.date(Order.created_at), func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    revenue = [{"date": str(r[0]), "value": float(r[1] or 0)} for r in revenue_result.all()]

    volume_result = await db.execute(
        select(func.date(Message.created_at), func.count(Message.id))
        .where(Message.created_at >= since)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    )
    message_volume = [{"date": str(r[0]), "count": r[1]} for r in volume_result.all()]

    platform_result = await db.execute(
        select(User.platform, func.count(User.id)).group_by(User.platform)
    )
    platform_breakdown = [{"name": str(r[0]), "value": r[1]} for r in platform_result.all()]

    return {
        "revenue": revenue,
        "message_volume": message_volume,
        "platform_breakdown": platform_breakdown,
    }


@router.get("/analytics/top-questions")
async def get_top_questions_admin(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Top 10 user questions/messages."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Message.content, func.count(Message.id).label("count"))
        .where(
            Message.created_at >= since,
            Message.role == "user",
            func.length(func.trim(Message.content)) > 0,
        )
        .group_by(Message.content)
        .order_by(desc("count"))
        .limit(10)
    )
    return [{"question": row[0], "count": row[1]} for row in result.all()]


@router.get("/settings")
async def get_admin_settings(_: dict = Depends(get_admin_user)):
    """Get admin dashboard settings."""
    return {
        **_admin_settings,
        "openai_api_key": _mask_secret(_admin_settings.get("openai_api_key")),
        "claude_api_key": _mask_secret(_admin_settings.get("claude_api_key")),
        "whatsapp_api_token": _mask_secret(_admin_settings.get("whatsapp_api_token")),
    }


@router.put("/settings")
async def update_admin_settings(
    request: AdminSettingsUpdateRequest,
    _: dict = Depends(get_admin_user),
):
    """Update admin dashboard settings."""
    data = request.model_dump(exclude_unset=True)
    _admin_settings.update(data)
    return {"message": "Settings saved", "updated_fields": list(data.keys())}


@router.post("/settings/test-connection")
async def test_admin_connections(_: dict = Depends(get_admin_user)):
    """Lightweight integration status check."""
    website_ok = bool(_admin_settings.get("website_api_url"))
    return {
        "status": "ok",
        "checks": {
            "openai": bool(_admin_settings.get("openai_api_key")),
            "claude": bool(_admin_settings.get("claude_api_key")),
            "whatsapp": bool(_admin_settings.get("whatsapp_api_token")),
            "website": website_ok,
        },
    }


@router.get("/analytics/top-intents")
async def get_top_intents(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get top detected intents."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Conversation.intent, func.count(Conversation.id))
        .where(
            Conversation.intent.isnot(None),
            Conversation.started_at >= since,
        )
        .group_by(Conversation.intent)
        .order_by(desc(func.count(Conversation.id)))
        .limit(10)
    )
    return [{"intent": row[0], "count": row[1]} for row in result.all()]


@router.get("/analytics/sentiment")
async def get_sentiment_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get sentiment distribution."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Conversation.sentiment, func.count(Conversation.id))
        .where(
            Conversation.sentiment.isnot(None),
            Conversation.started_at >= since,
        )
        .group_by(Conversation.sentiment)
    )
    return {row[0]: row[1] for row in result.all()}

"""
Admin router - dashboard data, overview, and management endpoints.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.models.order import Order
from app.models.campaign import Campaign
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
    import asyncio
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


@router.get("/users")
async def list_users(
    tier: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List users with filters."""
    query = select(User).order_by(desc(User.last_seen_at))
    if tier:
        query = query.where(User.tier == tier)
    if platform:
        query = query.where(User.platform == platform)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "name": u.name,
            "platform": u.platform,
            "tier": u.tier,
            "loyalty_points": u.loyalty_points,
            "purchase_count": u.purchase_count,
            "total_purchases": u.total_purchases,
            "is_active": u.is_active,
            "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
        }
        for u in users
    ]


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

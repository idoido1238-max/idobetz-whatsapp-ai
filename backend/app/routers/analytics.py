"""
Analytics router.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.analytics import AnalyticsEvent
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter()


@router.get("/events")
async def get_events(
    event_type: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get analytics events."""
    since = datetime.utcnow() - timedelta(days=days)
    query = select(AnalyticsEvent).where(AnalyticsEvent.created_at >= since)
    if event_type:
        query = query.where(AnalyticsEvent.event_type == event_type)
    query = query.order_by(desc(AnalyticsEvent.created_at)).limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "platform": e.platform,
            "user_id": e.user_id,
            "properties": e.properties,
            "value": e.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/messages-per-day")
async def get_messages_per_day(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get message count per day."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(Message.created_at >= since)
        .group_by(func.date(Message.created_at))
        .order_by("date")
    )
    return [{"date": str(row[0]), "count": row[1]} for row in result.all()]


@router.get("/response-times")
async def get_response_times(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get average AI response times."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            Message.ai_provider,
            func.avg(Message.processing_time_ms).label("avg_ms"),
            func.count(Message.id).label("count"),
        )
        .where(
            Message.created_at >= since,
            Message.ai_provider.isnot(None),
        )
        .group_by(Message.ai_provider)
    )
    return [
        {
            "provider": row[0],
            "avg_response_time_ms": round(row[1] or 0, 2),
            "message_count": row[2],
        }
        for row in result.all()
    ]


@router.get("/satisfaction-scores")
async def get_satisfaction_scores(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get customer satisfaction scores."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.avg(Conversation.satisfaction_rating).label("avg_score"),
            func.count(Conversation.id).label("total_rated"),
        )
        .where(
            Conversation.started_at >= since,
            Conversation.satisfaction_rating.isnot(None),
        )
    )
    row = result.first()
    return {
        "average_score": round(row[0] or 0, 2) if row else 0,
        "total_rated": row[1] if row else 0,
        "period_days": days,
    }


@router.get("/user-growth")
async def get_user_growth(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get user growth over time."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(User.first_seen_at).label("date"),
            func.count(User.id).label("new_users"),
        )
        .where(User.first_seen_at >= since)
        .group_by(func.date(User.first_seen_at))
        .order_by("date")
    )
    return [{"date": str(row[0]), "new_users": row[1]} for row in result.all()]

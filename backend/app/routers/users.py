"""
Users router.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_admin_user
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_users(
    platform: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """List users."""
    query = select(User).order_by(desc(User.last_seen_at))
    if platform:
        query = query.where(User.platform == platform)
    if tier:
        query = query.where(User.tier == tier)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "name": u.name,
            "phone_number": u.phone_number,
            "platform": u.platform,
            "tier": u.tier,
            "loyalty_points": u.loyalty_points,
            "purchase_count": u.purchase_count,
            "total_purchases": u.total_purchases,
            "language": u.language,
            "is_active": u.is_active,
            "opt_in_marketing": u.opt_in_marketing,
            "first_seen_at": u.first_seen_at.isoformat() if u.first_seen_at else None,
            "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
        }
        for u in users
    ]


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    """Get user details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "platform": user.platform,
        "tier": user.tier,
        "loyalty_points": user.loyalty_points,
        "purchase_count": user.purchase_count,
        "total_purchases": user.total_purchases,
        "language": user.language,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "opt_in_marketing": user.opt_in_marketing,
        "is_active": user.is_active,
        "is_blocked": user.is_blocked,
    }


@router.delete("/{user_id}")
async def delete_user_gdpr(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user),
):
    """GDPR: Delete user data."""
    from app.utils.audit_log import audit_logger
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    # Anonymize instead of hard delete for data integrity
    user.name = "Deleted User"
    user.email = None
    user.phone_number = None
    user.is_active = False
    user.metadata_ = None
    await db.commit()

    await audit_logger.log_data_deletion(user_id, current_user.get("sub", ""))
    return {"message": "User data deleted (GDPR compliant)"}

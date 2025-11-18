"""
Analytics routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict

from ...database import get_db
from ...models.session import VPNSession, SessionStatus
from ...models.engagement import Engagement
from ...models.user import User, UserRole
from ...api.routes.sessions import get_current_user

router = APIRouter()


@router.get("/dashboard", response_model=Dict)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.ENGAGEMENT_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Active sessions
    active_sessions_query = select(func.count(VPNSession.id)).where(
        VPNSession.status == SessionStatus.ACTIVE
    )
    if user.role != UserRole.PLATFORM_ADMIN:
        active_sessions_query = active_sessions_query.where(VPNSession.user_id == user.id)
    
    active_sessions = await db.execute(active_sessions_query)
    active_count = active_sessions.scalar() or 0
    
    # Total sessions (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    total_sessions_query = select(func.count(VPNSession.id)).where(
        VPNSession.created_at >= yesterday
    )
    if user.role != UserRole.PLATFORM_ADMIN:
        total_sessions_query = total_sessions_query.where(VPNSession.user_id == user.id)
    
    total_sessions = await db.execute(total_sessions_query)
    total_count = total_sessions.scalar() or 0
    
    # Total bandwidth
    bandwidth_query = select(
        func.sum(VPNSession.bytes_sent + VPNSession.bytes_received)
    ).where(VPNSession.status == SessionStatus.ACTIVE)
    if user.role != UserRole.PLATFORM_ADMIN:
        bandwidth_query = bandwidth_query.where(VPNSession.user_id == user.id)
    
    bandwidth_result = await db.execute(bandwidth_query)
    total_bandwidth = bandwidth_result.scalar() or 0
    
    # Active engagements
    engagements_query = select(func.count(Engagement.id)).where(
        Engagement.status.in_([EngagementStatus.APPROVED, EngagementStatus.ACTIVE])
    )
    if user.role != UserRole.PLATFORM_ADMIN:
        engagements_query = engagements_query.where(Engagement.owner_id == user.id)
    
    engagements_result = await db.execute(engagements_query)
    active_engagements = engagements_result.scalar() or 0
    
    return {
        "active_sessions": active_count,
        "total_sessions_24h": total_count,
        "total_bandwidth_bytes": total_bandwidth,
        "active_engagements": active_engagements,
        "timestamp": datetime.utcnow().isoformat()
    }


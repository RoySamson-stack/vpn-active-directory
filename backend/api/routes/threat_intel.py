"""
Threat Intelligence routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select, and_

from ...database import get_db
from ...models.threat_intel import ThreatIntel, ThreatType
from ...models.user import User, UserRole
from ...api.routes.sessions import get_current_user

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_threats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    threat_type: Optional[str] = None,
    limit: int = 100
):
    """List threat intelligence indicators"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = select(ThreatIntel)
    
    if threat_type:
        try:
            query = query.where(ThreatIntel.threat_type == ThreatType(threat_type))
        except ValueError:
            pass
    
    query = query.where(ThreatIntel.is_blocked == True).limit(limit)
    
    result = await db.execute(query)
    threats = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "indicator": t.indicator,
            "threat_type": t.threat_type.value,
            "source": t.source,
            "severity": t.severity,
            "confidence": t.confidence,
            "is_blocked": t.is_blocked,
            "created_at": t.created_at.isoformat()
        }
        for t in threats
    ]


@router.get("/check/{indicator}", response_model=dict)
async def check_indicator(
    indicator: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if indicator is in threat intelligence"""
    result = await db.execute(
        select(ThreatIntel).where(
            and_(
                ThreatIntel.indicator == indicator,
                ThreatIntel.is_blocked == True
            )
        )
    )
    threat = result.scalar_one_or_none()
    
    return {
        "indicator": indicator,
        "is_blocked": threat is not None,
        "threat": {
            "severity": threat.severity,
            "confidence": threat.confidence,
            "source": threat.source
        } if threat else None
    }


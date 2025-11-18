"""
Engagement routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from sqlalchemy import select
from datetime import datetime

from ...database import get_db
from ...utils.security import verify_token
from ...models.engagement import Engagement, EngagementStatus
from ...models.user import User, UserRole
from ...api.routes.sessions import get_current_user

router = APIRouter()
security = HTTPBearer()


class CreateEngagementRequest(BaseModel):
    name: str
    description: Optional[str] = None
    client_name: str
    client_contact: Optional[str] = None
    contract_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    scope: Optional[dict] = None
    max_concurrent_sessions: int = 5


class UpdateEngagementRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[datetime] = None


@router.post("/", response_model=dict)
async def create_engagement(
    request: CreateEngagementRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new engagement"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.ENGAGEMENT_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    import secrets
    engagement_id = f"ENG-{secrets.token_hex(8).upper()}"
    
    engagement = Engagement(
        engagement_id=engagement_id,
        name=request.name,
        description=request.description,
        owner_id=user.id,
        client_name=request.client_name,
        client_contact=request.client_contact,
        contract_number=request.contract_number,
        start_date=request.start_date,
        end_date=request.end_date,
        scope=request.scope,
        max_concurrent_sessions=request.max_concurrent_sessions,
        status=EngagementStatus.DRAFT
    )
    
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)
    
    return {
        "id": engagement.id,
        "engagement_id": engagement.engagement_id,
        "name": engagement.name,
        "status": engagement.status.value
    }


@router.get("/", response_model=List[dict])
async def list_engagements(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = None
):
    """List engagements"""
    query = select(Engagement)
    
    # Filter by user role
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.AUDITOR]:
        query = query.where(Engagement.owner_id == user.id)
    
    if status_filter:
        try:
            status_enum = EngagementStatus(status_filter)
            query = query.where(Engagement.status == status_enum)
        except ValueError:
            pass
    
    query = query.order_by(Engagement.created_at.desc())
    
    result = await db.execute(query)
    engagements = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "engagement_id": e.engagement_id,
            "name": e.name,
            "client_name": e.client_name,
            "status": e.status.value,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None
        }
        for e in engagements
    ]


@router.get("/{engagement_id}", response_model=dict)
async def get_engagement(
    engagement_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get engagement details"""
    result = await db.execute(
        select(Engagement).where(Engagement.engagement_id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )
    
    # Check permissions
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.AUDITOR] and engagement.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": engagement.id,
        "engagement_id": engagement.engagement_id,
        "name": engagement.name,
        "description": engagement.description,
        "client_name": engagement.client_name,
        "status": engagement.status.value,
        "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
        "end_date": engagement.end_date.isoformat() if engagement.end_date else None,
        "scope": engagement.scope
    }


@router.patch("/{engagement_id}", response_model=dict)
async def update_engagement(
    engagement_id: str,
    request: UpdateEngagementRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update engagement"""
    result = await db.execute(
        select(Engagement).where(Engagement.engagement_id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )
    
    # Check permissions
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.ENGAGEMENT_LEAD]:
        if engagement.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Update fields
    if request.name:
        engagement.name = request.name
    if request.description:
        engagement.description = request.description
    if request.status:
        try:
            engagement.status = EngagementStatus(request.status)
        except ValueError:
            pass
    if request.end_date:
        engagement.end_date = request.end_date
    
    await db.commit()
    await db.refresh(engagement)
    
    return {
        "id": engagement.id,
        "engagement_id": engagement.engagement_id,
        "status": engagement.status.value
    }


@router.post("/{engagement_id}/approve", response_model=dict)
async def approve_engagement(
    engagement_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve engagement"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.ENGAGEMENT_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    result = await db.execute(
        select(Engagement).where(Engagement.engagement_id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )
    
    engagement.status = EngagementStatus.APPROVED
    engagement.approved_at = datetime.utcnow()
    engagement.authorized_by = user.username
    
    await db.commit()
    
    return {"message": "Engagement approved", "status": engagement.status.value}


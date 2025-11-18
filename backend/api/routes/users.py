"""
User routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select

from ...database import get_db
from ...models.user import User, UserRole
from ...api.routes.sessions import get_current_user

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List users"""
    if user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active
        }
        for u in users
    ]


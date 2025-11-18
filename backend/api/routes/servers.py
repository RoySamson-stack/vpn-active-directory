"""
VPN Server routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select

from ...database import get_db
from ...models.server import VPNServer
from ...models.user import User, UserRole
from ...api.routes.sessions import get_current_user

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_servers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    region: str = None
):
    """List VPN servers"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = select(VPNServer)
    if region:
        query = query.where(VPNServer.region == region)
    
    result = await db.execute(query)
    servers = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "server_id": s.server_id,
            "hostname": s.hostname,
            "region": s.region,
            "status": s.status.value,
            "current_connections": s.current_connections,
            "max_connections": s.max_connections,
            "wireguard_enabled": s.wireguard_enabled,
            "ipsec_enabled": s.ipsec_enabled
        }
        for s in servers
    ]


@router.get("/{server_id}", response_model=dict)
async def get_server(
    server_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get server details"""
    if user.role not in [UserRole.PLATFORM_ADMIN, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    result = await db.execute(
        select(VPNServer).where(VPNServer.server_id == server_id)
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return {
        "id": server.id,
        "server_id": server.server_id,
        "hostname": server.hostname,
        "ip_address": server.ip_address,
        "public_ip": server.public_ip,
        "region": server.region,
        "status": server.status.value,
        "current_connections": server.current_connections,
        "max_connections": server.max_connections,
        "wireguard_enabled": server.wireguard_enabled,
        "ipsec_enabled": server.ipsec_enabled
    }


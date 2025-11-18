"""
VPN Session routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from sqlalchemy import select, and_

from ...database import get_db
from ...utils.security import verify_token
from ...models.session import VPNSession
from ...models.user import User, UserRole
from ...services.vpn.session_manager import SessionManager

router = APIRouter()
security = HTTPBearer()
session_manager = SessionManager()


class CreateSessionRequest(BaseModel):
    engagement_id: Optional[int] = None
    client_public_key: str
    client_ip: str
    protocol: str = "wireguard"
    hop_count: int = 1


class SessionResponse(BaseModel):
    session_id: str
    status: str
    server_public_key: str
    preshared_key: str
    server_ip: str
    server_port: int
    hop_path: Optional[List[int]] = None
    config: Optional[str] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    result = await db.execute(
        select(User).where(User.id == payload.get("user_id"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new VPN session"""
    session = await session_manager.create_session(
        db,
        user.id,
        request.engagement_id,
        request.client_public_key,
        request.client_ip,
        request.protocol,
        request.hop_count
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create session"
        )
    
    # Get server info
    from ...models.server import VPNServer
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == session.server_id)
    )
    server = result.scalar_one_or_none()
    
    # Generate client config
    from ...services.vpn.wireguard_service import WireGuardService
    wg = WireGuardService()
    config = wg.create_peer_config(
        request.client_public_key,
        session.server_public_key,
        server.public_ip if server else "0.0.0.0",
        server.wireguard_port if server else 51820,
        ["0.0.0.0/0"],
        session.preshared_key
    )
    
    return SessionResponse(
        session_id=session.session_id,
        status=session.status.value,
        server_public_key=session.server_public_key,
        preshared_key=session.preshared_key,
        server_ip=server.public_ip if server else "0.0.0.0",
        server_port=server.wireguard_port if server else 51820,
        hop_path=session.hop_path,
        config=config
    )


@router.get("/", response_model=List[dict])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """List VPN sessions"""
    query = select(VPNSession)
    
    # Filter by user role
    if user.role != UserRole.PLATFORM_ADMIN:
        query = query.where(VPNSession.user_id == user.id)
    
    query = query.order_by(VPNSession.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "status": s.status.value,
            "protocol": s.protocol,
            "hop_count": s.hop_count,
            "created_at": s.created_at.isoformat(),
            "connected_at": s.connected_at.isoformat() if s.connected_at else None,
            "bytes_sent": s.bytes_sent,
            "bytes_received": s.bytes_received,
            "risk_score": s.risk_score
        }
        for s in sessions
    ]


@router.get("/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session details"""
    result = await db.execute(
        select(VPNSession).where(VPNSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check permissions
    if user.role != UserRole.PLATFORM_ADMIN and session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    stats = await session_manager.get_session_stats(db, session_id)
    return stats or {}


@router.delete("/{session_id}")
async def terminate_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Terminate VPN session"""
    result = await db.execute(
        select(VPNSession).where(VPNSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check permissions
    if user.role != UserRole.PLATFORM_ADMIN and session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = await session_manager.terminate_session(db, session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to terminate session"
        )
    
    return {"message": "Session terminated"}


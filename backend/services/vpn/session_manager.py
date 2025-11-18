"""
VPN Session Manager
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ...models.session import VPNSession, SessionStatus
from ...models.server import VPNServer, ServerStatus
from ...models.engagement import Engagement, EngagementStatus
from ...utils.security import generate_session_id, calculate_risk_score
from ...utils.crypto import generate_key_pair, derive_preshared_key
from .wireguard_service import WireGuardService
from .multi_hop_service import MultiHopService
from ...config import get_settings

settings = get_settings()


class SessionManager:
    """VPN Session Manager"""
    
    def __init__(self):
        self.wireguard = WireGuardService()
        self.multi_hop = MultiHopService()
    
    async def create_session(
        self,
        db: AsyncSession,
        user_id: int,
        engagement_id: Optional[int],
        client_public_key: str,
        client_ip: str,
        protocol: str = "wireguard",
        hop_count: int = 1
    ) -> Optional[VPNSession]:
        """Create new VPN session"""
        try:
            # Validate engagement if provided
            if engagement_id:
                result = await db.execute(
                    select(Engagement).where(
                        and_(
                            Engagement.id == engagement_id,
                            Engagement.status == EngagementStatus.APPROVED
                        )
                    )
                )
                engagement = result.scalar_one_or_none()
                if not engagement:
                    return None
                
                # Check engagement dates
                if engagement.end_date and engagement.end_date < datetime.utcnow():
                    return None
            
            # Select ingress server
            server = await self._select_ingress_server(db)
            if not server:
                return None
            
            # Generate keys
            server_private_key, server_public_key = generate_key_pair()
            preshared_key = derive_preshared_key()
            
            # Create session
            session = VPNSession(
                user_id=user_id,
                engagement_id=engagement_id,
                server_id=server.id,
                session_id=generate_session_id(),
                client_ip=client_ip,
                client_public_key=client_public_key,
                server_public_key=server_public_key,
                server_private_key=server_private_key,  # Should be encrypted
                preshared_key=preshared_key,  # Should be encrypted
                status=SessionStatus.PENDING,
                protocol=protocol,
                hop_count=hop_count,
                connected_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # Configure multi-hop if enabled
            if settings.vpn_multi_hop_enabled and hop_count > 1:
                hop_path = await self.multi_hop.select_hop_path(
                    db, server.id, hop_count
                )
                await self.multi_hop.configure_hop_routing(db, session, hop_path)
            
            # Add peer to WireGuard
            if protocol == "wireguard":
                allowed_ips = ["0.0.0.0/0"]  # Route all traffic
                self.wireguard.add_peer(
                    client_public_key,
                    allowed_ips,
                    preshared_key
                )
            
            # Calculate initial risk score
            risk_data = {
                'ip_in_threat_intel': False,  # Would check threat intel
                'unusual_time': False,
                'device_compliant': True,
                'engagement_authorized': engagement_id is not None,
                'mfa_verified': True
            }
            session.risk_score = calculate_risk_score(risk_data)
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # Update server connection count
            server.current_connections += 1
            await db.commit()
            
            return session
        except Exception as e:
            print(f"Error creating session: {e}")
            await db.rollback()
            return None
    
    async def _select_ingress_server(self, db: AsyncSession) -> Optional[VPNServer]:
        """Select best ingress server based on load"""
        result = await db.execute(
            select(VPNServer).where(
                and_(
                    VPNServer.status == ServerStatus.ACTIVE,
                    VPNServer.can_ingress == True,
                    VPNServer.current_connections < VPNServer.max_connections
                )
            ).order_by(
                VPNServer.current_connections.asc()
            )
        )
        return result.scalar_one_or_none()
    
    async def terminate_session(
        self,
        db: AsyncSession,
        session_id: str
    ) -> bool:
        """Terminate VPN session"""
        try:
            result = await db.execute(
                select(VPNSession).where(VPNSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            # Remove peer from WireGuard
            if session.protocol == "wireguard":
                self.wireguard.remove_peer(session.client_public_key)
            
            # Update session
            session.status = SessionStatus.TERMINATED
            session.disconnected_at = datetime.utcnow()
            
            # Update server connection count
            if session.server:
                session.server.current_connections = max(
                    0, session.server.current_connections - 1
                )
            
            await db.commit()
            return True
        except Exception as e:
            print(f"Error terminating session: {e}")
            await db.rollback()
            return False
    
    async def get_session_stats(self, db: AsyncSession, session_id: str) -> Optional[Dict]:
        """Get session statistics"""
        result = await db.execute(
            select(VPNSession).where(VPNSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Get real-time stats from WireGuard if available
        wg_stats = None
        if session.protocol == "wireguard" and session.status == SessionStatus.ACTIVE:
            wg_status = self.wireguard.get_interface_status()
            if wg_status:
                peer = next(
                    (p for p in wg_status['peers'] if p['public_key'] == session.client_public_key),
                    None
                )
                if peer:
                    wg_stats = peer['transfer']
        
        return {
            'session_id': session.session_id,
            'status': session.status.value,
            'bytes_sent': session.bytes_sent,
            'bytes_received': session.bytes_received,
            'packets_sent': session.packets_sent,
            'packets_received': session.packets_received,
            'risk_score': session.risk_score,
            'connected_at': session.connected_at.isoformat() if session.connected_at else None,
            'wireguard_stats': wg_stats
        }


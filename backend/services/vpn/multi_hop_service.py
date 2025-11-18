"""
Multi-hop routing service
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ...models.server import VPNServer, ServerStatus
from ...models.session import VPNSession
from ...config import get_settings
import random

settings = get_settings()


class MultiHopService:
    """Multi-hop routing service for enhanced privacy"""
    
    def __init__(self):
        self.max_hops = settings.vpn_max_hops
    
    async def select_hop_path(
        self,
        db: AsyncSession,
        ingress_server_id: int,
        hop_count: int = 2,
        region_preference: Optional[str] = None
    ) -> List[int]:
        """Select optimal multi-hop path"""
        if hop_count < 2:
            return [ingress_server_id]
        
        hop_count = min(hop_count, self.max_hops)
        
        # Get available servers
        query = select(VPNServer).where(
            and_(
                VPNServer.status == ServerStatus.ACTIVE,
                VPNServer.can_relay == True,
                VPNServer.id != ingress_server_id
            )
        )
        
        if region_preference:
            query = query.where(VPNServer.region == region_preference)
        
        result = await db.execute(query)
        available_servers = result.scalars().all()
        
        if not available_servers:
            return [ingress_server_id]
        
        # Select servers based on load
        servers_by_load = sorted(
            available_servers,
            key=lambda s: s.current_connections / max(s.max_connections, 1)
        )
        
        # Select unique servers for the path
        selected = [ingress_server_id]
        remaining_servers = [s.id for s in servers_by_load if s.id != ingress_server_id]
        
        # Add relay servers
        for _ in range(hop_count - 2):
            if remaining_servers:
                # Prefer servers with lower load
                selected.append(remaining_servers.pop(0))
        
        # Add egress server (last hop)
        egress_servers = [
            s.id for s in available_servers
            if s.can_egress and s.id not in selected
        ]
        if egress_servers:
            selected.append(random.choice(egress_servers))
        elif remaining_servers:
            selected.append(remaining_servers[0])
        
        return selected[:hop_count]
    
    async def configure_hop_routing(
        self,
        db: AsyncSession,
        session: VPNSession,
        hop_path: List[int]
    ) -> bool:
        """Configure routing for multi-hop path"""
        try:
            # Update session with hop path
            session.hop_path = hop_path
            session.hop_count = len(hop_path)
            
            # Get server details for each hop
            servers = []
            for server_id in hop_path:
                result = await db.execute(
                    select(VPNServer).where(VPNServer.id == server_id)
                )
                server = result.scalar_one_or_none()
                if server:
                    servers.append(server)
            
            # Configure routing rules (implementation depends on network setup)
            # This would typically involve:
            # 1. Setting up WireGuard peer relationships between hops
            # 2. Configuring iptables rules for traffic forwarding
            # 3. Setting up routing tables
            
            await db.commit()
            return True
        except Exception as e:
            print(f"Error configuring hop routing: {e}")
            await db.rollback()
            return False
    
    def generate_hop_config(
        self,
        hop_path: List[int],
        servers: List[Dict],
        client_config: Dict
    ) -> Dict:
        """Generate configuration for multi-hop client"""
        config = {
            'hops': [],
            'client_config': client_config
        }
        
        for i, server_id in enumerate(hop_path):
            server = next((s for s in servers if s['id'] == server_id), None)
            if server:
                hop_config = {
                    'hop_number': i + 1,
                    'server_id': server_id,
                    'server_ip': server['public_ip'],
                    'server_port': server.get('wireguard_port', 51820),
                    'public_key': server['public_key'],
                    'is_egress': i == len(hop_path) - 1
                }
                config['hops'].append(hop_config)
        
        return config


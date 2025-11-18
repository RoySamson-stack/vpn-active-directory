"""
VPN Server model
"""
from sqlalchemy import Column, String, Integer, Enum, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, TimestampMixin


class ServerStatus(PyEnum):
    """Server status"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    DRAINING = "draining"


class VPNServer(Base, TimestampMixin):
    """VPN Server model"""
    __tablename__ = "vpn_servers"
    
    server_id = Column(String(255), unique=True, index=True, nullable=False)
    hostname = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    public_ip = Column(String(45), nullable=False)
    
    region = Column(String(100), nullable=False)
    datacenter = Column(String(100))
    
    status = Column(Enum(ServerStatus), default=ServerStatus.ACTIVE, nullable=False)
    
    # Protocol support
    wireguard_enabled = Column(Boolean, default=True)
    ipsec_enabled = Column(Boolean, default=False)
    
    # Configuration
    wireguard_port = Column(Integer, default=51820)
    ipsec_port = Column(Integer, default=500)
    public_key = Column(String(255), nullable=False)
    private_key = Column(String(255))  # Encrypted
    
    # Capabilities
    can_ingress = Column(Boolean, default=True)  # Can accept client connections
    can_relay = Column(Boolean, default=True)  # Can relay traffic
    can_egress = Column(Boolean, default=True)  # Can be exit node
    
    # Load metrics
    current_connections = Column(Integer, default=0)
    max_connections = Column(Integer, default=1000)
    bandwidth_used = Column(Integer, default=0)  # Bytes
    
    # Metadata
    tags = Column(JSON)  # For routing preferences
    config = Column(JSON)  # Additional configuration
    
    # Relationships
    sessions = relationship("VPNSession", back_populates="server")
    
    def __repr__(self):
        return f"<VPNServer(server_id={self.server_id}, region={self.region})>"


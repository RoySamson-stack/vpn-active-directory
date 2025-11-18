"""
VPN Session model
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from .base import Base, TimestampMixin


class SessionStatus(PyEnum):
    """Session status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class VPNSession(Base, TimestampMixin):
    """VPN Session model"""
    __tablename__ = "vpn_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    engagement_id = Column(Integer, ForeignKey("engagements.id"))
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))
    
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    client_ip = Column(String(45))  # IPv6 compatible
    client_public_key = Column(String(255), nullable=False)
    server_public_key = Column(String(255), nullable=False)
    server_private_key = Column(String(255))  # Encrypted
    preshared_key = Column(String(255))  # Encrypted
    
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
    protocol = Column(String(50), default="wireguard", nullable=False)  # wireguard, ipsec
    
    # Multi-hop configuration
    hop_count = Column(Integer, default=1, nullable=False)
    hop_path = Column(JSON)  # List of server IDs in the path
    
    # Traffic statistics
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    packets_sent = Column(Integer, default=0)
    packets_received = Column(Integer, default=0)
    
    # Timestamps
    connected_at = Column(DateTime(timezone=True))
    disconnected_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Metadata
    client_info = Column(JSON)  # Client device info
    risk_score = Column(Integer, default=0)  # Real-time risk scoring
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    engagement = relationship("Engagement", back_populates="sessions")
    server = relationship("VPNServer", back_populates="sessions")
    
    def __repr__(self):
        return f"<VPNSession(session_id={self.session_id}, status={self.status})>"


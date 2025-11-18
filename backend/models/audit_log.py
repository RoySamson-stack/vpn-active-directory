"""
Audit Log model for compliance
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Audit Log model for immutable compliance logging"""
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("vpn_sessions.id"))
    engagement_id = Column(Integer, ForeignKey("engagements.id"))
    
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255))
    
    # Details
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    
    # Integrity
    signature = Column(String(512))  # Cryptographic signature
    previous_hash = Column(String(512))  # For Merkle tree
    
    # Relationships
    user = relationship("User")
    session = relationship("VPNSession")
    engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id})>"


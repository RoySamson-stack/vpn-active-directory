"""
Engagement model for pentesting contracts
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from .base import Base, TimestampMixin


class EngagementStatus(PyEnum):
    """Engagement status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Engagement(Base, TimestampMixin):
    """Engagement model for tracking pentesting contracts"""
    __tablename__ = "engagements"
    
    engagement_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    client_name = Column(String(255), nullable=False)
    client_contact = Column(String(255))
    contract_number = Column(String(255))
    
    status = Column(Enum(EngagementStatus), default=EngagementStatus.DRAFT, nullable=False)
    
    # Authorization
    authorized_by = Column(String(255))  # Person who authorized
    authorization_document = Column(Text)  # Path to authorization document
    scope = Column(JSON)  # Defined scope of testing
    
    # Dates
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Configuration
    allowed_ips = Column(JSON)  # Allowed source IPs
    allowed_domains = Column(JSON)  # Allowed target domains
    max_concurrent_sessions = Column(Integer, default=5)
    require_mfa = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="engagements")
    sessions = relationship("VPNSession", back_populates="engagement")
    
    def __repr__(self):
        return f"<Engagement(engagement_id={self.engagement_id}, status={self.status})>"


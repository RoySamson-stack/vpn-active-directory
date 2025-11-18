"""
User model
"""
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, TimestampMixin


class UserRole(PyEnum):
    """User roles"""
    PLATFORM_ADMIN = "platform_admin"
    ENGAGEMENT_LEAD = "engagement_lead"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    CLIENT_VIEWER = "client_viewer"


class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    ad_dn = Column(String(512), unique=True, index=True)  # Active Directory Distinguished Name
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255))
    last_login = Column(String(255))
    
    # Relationships
    sessions = relationship("VPNSession", back_populates="user")
    engagements = relationship("Engagement", back_populates="owner")
    
    def __repr__(self):
        return f"<User(username={self.username}, role={self.role})>"


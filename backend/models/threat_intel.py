"""
Threat Intelligence model
"""
from sqlalchemy import Column, String, Integer, Enum, DateTime, Text, Boolean, Index
from enum import Enum as PyEnum
from datetime import datetime
from .base import Base, TimestampMixin


class ThreatType(PyEnum):
    """Threat type"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"
    EMAIL = "email"


class ThreatIntel(Base, TimestampMixin):
    """Threat Intelligence model"""
    __tablename__ = "threat_intel"
    
    indicator = Column(String(512), nullable=False, index=True)
    threat_type = Column(Enum(ThreatType), nullable=False)
    
    source = Column(String(255), nullable=False)  # virustotal, abuseipdb, etc.
    severity = Column(Integer, default=5)  # 1-10 scale
    confidence = Column(Integer, default=5)  # 1-10 scale
    
    description = Column(Text)
    metadata = Column(Text)  # JSON string
    
    is_blocked = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_indicator_type', 'indicator', 'threat_type'),
    )
    
    def __repr__(self):
        return f"<ThreatIntel(indicator={self.indicator}, type={self.threat_type})>"


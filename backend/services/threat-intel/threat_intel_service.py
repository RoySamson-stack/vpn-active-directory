"""
Threat Intelligence service
"""
import httpx
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from ...models.threat_intel import ThreatIntel, ThreatType
from ...config import get_settings

settings = get_settings()


class ThreatIntelService:
    """Threat Intelligence service"""
    
    def __init__(self):
        self.virustotal_api_key = settings.virustotal_api_key
        self.abuseipdb_api_key = settings.abuseipdb_api_key
    
    async def check_ip(self, ip_address: str, db: AsyncSession) -> bool:
        """Check if IP address is in threat intelligence"""
        # Check local database first
        result = await db.execute(
            select(ThreatIntel).where(
                ThreatIntel.indicator == ip_address,
                ThreatIntel.threat_type == ThreatType.IP_ADDRESS,
                ThreatIntel.is_blocked == True
            )
        )
        threat = result.scalar_one_or_none()
        
        if threat:
            return True
        
        # Check external sources if enabled
        if settings.threat_intel_enabled:
            # Check AbuseIPDB
            if self.abuseipdb_api_key:
                abuse_result = await self._check_abuseipdb(ip_address)
                if abuse_result and abuse_result.get('is_abuse'):
                    # Store in database
                    threat = ThreatIntel(
                        indicator=ip_address,
                        threat_type=ThreatType.IP_ADDRESS,
                        source="abuseipdb",
                        severity=abuse_result.get('abuse_confidence', 5),
                        confidence=abuse_result.get('abuse_confidence', 5),
                        is_blocked=True,
                        expires_at=datetime.utcnow() + timedelta(days=30)
                    )
                    db.add(threat)
                    await db.commit()
                    return True
        
        return False
    
    async def _check_abuseipdb(self, ip_address: str) -> Optional[Dict]:
        """Check IP against AbuseIPDB"""
        if not self.abuseipdb_api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={
                        "ipAddress": ip_address,
                        "maxAgeInDays": 90,
                        "verbose": ""
                    },
                    headers={
                        "Key": self.abuseipdb_api_key,
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        return {
                            "is_abuse": data["data"].get("abuseConfidencePercentage", 0) > 0,
                            "abuse_confidence": data["data"].get("abuseConfidencePercentage", 0)
                        }
        except Exception as e:
            print(f"AbuseIPDB check error: {e}")
        
        return None
    
    async def check_domain(self, domain: str, db: AsyncSession) -> bool:
        """Check if domain is in threat intelligence"""
        result = await db.execute(
            select(ThreatIntel).where(
                ThreatIntel.indicator == domain,
                ThreatIntel.threat_type == ThreatType.DOMAIN,
                ThreatIntel.is_blocked == True
            )
        )
        threat = result.scalar_one_or_none()
        return threat is not None
    
    async def add_threat(
        self,
        db: AsyncSession,
        indicator: str,
        threat_type: ThreatType,
        source: str,
        severity: int = 5,
        confidence: int = 5
    ) -> ThreatIntel:
        """Add threat indicator to database"""
        threat = ThreatIntel(
            indicator=indicator,
            threat_type=threat_type,
            source=source,
            severity=severity,
            confidence=confidence,
            is_blocked=True,
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        db.add(threat)
        await db.commit()
        await db.refresh(threat)
        return threat


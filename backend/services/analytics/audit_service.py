"""
Audit logging service for compliance
"""
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from ...models.audit_log import AuditLog
from ...utils.security import generate_audit_signature
from ...config import get_settings

settings = get_settings()


class AuditService:
    """Audit logging service"""
    
    async def log_action(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        session_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an action to audit trail"""
        # Get previous hash for Merkle tree
        result = await db.execute(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
        )
        previous_log = result.scalar_one_or_none()
        previous_hash = previous_log.signature if previous_log else None
        
        # Create audit log entry
        log_data = f"{user_id}:{action}:{resource_type}:{resource_id}:{datetime.utcnow().isoformat()}"
        signature = generate_audit_signature(log_data, previous_hash)
        
        audit_log = AuditLog(
            user_id=user_id,
            session_id=session_id,
            engagement_id=engagement_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            signature=signature,
            previous_hash=previous_hash
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        return audit_log
    
    async def get_audit_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """Get audit logs with filters"""
        query = select(AuditLog)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()


"""
Active Directory authentication service
"""
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.user import User, UserRole
from .ldap_client import LDAPClient
from .radius_client import RADIUSClient
from ...config import get_settings

settings = get_settings()


class ADAuthService:
    """Active Directory authentication service"""
    
    def __init__(self):
        self.ldap_client = LDAPClient()
        self.radius_client = RADIUSClient()
    
    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        use_radius: bool = False
    ) -> Optional[User]:
        """Authenticate user via AD and sync to local database"""
        # Authenticate against AD
        if use_radius:
            radius_result = self.radius_client.authenticate(username, password)
            if not radius_result.get('authenticated'):
                return None
            user_info = self.ldap_client.get_user_info(
                self.ldap_client.find_user(username)
            )
        else:
            user_info = self.ldap_client.authenticate(username, password)
            if not user_info:
                return None
        
        # Check if user exists in local DB
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if user:
            # Update user info from AD
            user.email = user_info.get('email') or user.email
            user.full_name = user_info.get('full_name') or user.full_name
            user.ad_dn = user_info.get('dn')
            user.is_active = not user_info.get('disabled', False)
        else:
            # Create new user
            user = User(
                username=username,
                email=user_info.get('email', f"{username}@example.com"),
                full_name=user_info.get('full_name', username),
                ad_dn=user_info.get('dn'),
                role=UserRole.OPERATOR,  # Default role
                is_active=not user_info.get('disabled', False)
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        
        return user if user.is_active else None
    
    async def get_user_groups(self, username: str) -> list:
        """Get user's AD groups"""
        return self.ldap_client.get_user_groups(username)
    
    async def check_group_membership(self, username: str, group_dn: str) -> bool:
        """Check if user is member of a group"""
        return self.ldap_client.check_group_membership(username, group_dn)


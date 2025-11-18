"""
LDAP client for Active Directory integration
"""
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException
from typing import Optional, Dict, List
import ssl
from ..config import get_settings

settings = get_settings()


class LDAPClient:
    """LDAP client for Active Directory"""
    
    def __init__(self):
        self.server_url = settings.ad_server
        self.base_dn = settings.ad_base_dn
        self.bind_user = settings.ad_bind_user
        self.bind_password = settings.ad_bind_password
        self.ssl_enabled = settings.ad_ssl_enabled
        self.ssl_verify = settings.ad_ssl_verify
        
    def _get_server(self) -> Server:
        """Get LDAP server instance"""
        if self.ssl_enabled:
            tls = Tls(validate=ssl.CERT_REQUIRED if self.ssl_verify else ssl.CERT_NONE)
            return Server(self.server_url, use_ssl=True, tls=tls, get_info=ALL)
        return Server(self.server_url, get_info=ALL)
    
    def _get_connection(self, user: Optional[str] = None, password: Optional[str] = None) -> Connection:
        """Get LDAP connection"""
        server = self._get_server()
        bind_dn = user or self.bind_user
        bind_pw = password or self.bind_password
        
        conn = Connection(server, bind_dn, bind_pw, auto_bind=True)
        return conn
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user against AD"""
        try:
            # Search for user
            user_dn = self.find_user(username)
            if not user_dn:
                return None
            
            # Try to bind with user credentials
            conn = self._get_connection(user_dn, password)
            if conn.bound:
                # Get user attributes
                user_info = self.get_user_info(user_dn)
                conn.unbind()
                return user_info
            return None
        except LDAPException as e:
            print(f"LDAP authentication error: {e}")
            return None
    
    def find_user(self, username: str) -> Optional[str]:
        """Find user DN by username"""
        try:
            conn = self._get_connection()
            search_filter = f"(sAMAccountName={username})"
            
            conn.search(
                self.base_dn,
                search_filter,
                search_scope=SUBTREE,
                attributes=['distinguishedName', 'sAMAccountName', 'mail', 'displayName']
            )
            
            if conn.entries:
                return str(conn.entries[0].distinguishedName)
            return None
        except LDAPException as e:
            print(f"LDAP search error: {e}")
            return None
        finally:
            if conn:
                conn.unbind()
    
    def get_user_info(self, user_dn: str) -> Optional[Dict]:
        """Get user information from AD"""
        try:
            conn = self._get_connection()
            conn.search(
                user_dn,
                "(objectClass=user)",
                attributes=['sAMAccountName', 'mail', 'displayName', 'memberOf', 'userAccountControl']
            )
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    'dn': user_dn,
                    'username': str(entry.sAMAccountName) if entry.sAMAccountName else None,
                    'email': str(entry.mail) if entry.mail else None,
                    'full_name': str(entry.displayName) if entry.displayName else None,
                    'groups': [str(g) for g in entry.memberOf] if entry.memberOf else [],
                    'disabled': bool(int(entry.userAccountControl) & 0x0002) if entry.userAccountControl else False
                }
            return None
        except LDAPException as e:
            print(f"LDAP get user info error: {e}")
            return None
        finally:
            if conn:
                conn.unbind()
    
    def get_user_groups(self, username: str) -> List[str]:
        """Get user's AD groups"""
        try:
            user_dn = self.find_user(username)
            if not user_dn:
                return []
            
            user_info = self.get_user_info(user_dn)
            return user_info.get('groups', []) if user_info else []
        except Exception as e:
            print(f"Error getting user groups: {e}")
            return []
    
    def check_group_membership(self, username: str, group_dn: str) -> bool:
        """Check if user is member of a group"""
        groups = self.get_user_groups(username)
        return group_dn in groups


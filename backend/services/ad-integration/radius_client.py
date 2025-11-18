"""
RADIUS client for authentication
"""
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept, AccessReject
import socket
from typing import Optional, Dict
from ..config import get_settings

settings = get_settings()


class RADIUSClient:
    """RADIUS client for authentication"""
    
    def __init__(self):
        self.server = settings.radius_server
        self.port = settings.radius_port
        self.secret = settings.radius_secret.encode()
        self.dict = Dictionary("dictionary")
    
    def authenticate(self, username: str, password: str, nas_ip: str = "127.0.0.1") -> Optional[Dict]:
        """Authenticate user via RADIUS"""
        try:
            client = Client(
                server=self.server,
                authport=self.port,
                secret=self.secret,
                dict=self.dict
            )
            
            req = client.CreateAuthPacket(
                code=AccessRequest,
                User_Name=username,
                NAS_IP_Address=socket.inet_aton(nas_ip)
            )
            req["User-Password"] = req.PwCrypt(password)
            
            reply = client.SendPacket(req)
            
            if reply.code == AccessAccept:
                return {
                    'authenticated': True,
                    'attributes': dict(reply)
                }
            elif reply.code == AccessReject:
                return {
                    'authenticated': False,
                    'reason': 'Access rejected'
                }
            else:
                return {
                    'authenticated': False,
                    'reason': 'Unknown response'
                }
        except Exception as e:
            print(f"RADIUS authentication error: {e}")
            return {
                'authenticated': False,
                'reason': str(e)
            }


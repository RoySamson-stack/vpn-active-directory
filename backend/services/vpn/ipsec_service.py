"""
IPSec VPN service
"""
import subprocess
import os
from typing import Dict, Optional, List
from pathlib import Path
from ...utils.crypto import generate_ipsec_psk, generate_certificate_cn
from ...config import get_settings

settings = get_settings()


class IPSecService:
    """IPSec VPN service using StrongSwan"""
    
    def __init__(self):
        self.config_path = Path("/etc/ipsec.d")
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.secrets_path = Path("/etc/ipsec.secrets")
    
    def create_connection_config(
        self,
        connection_name: str,
        client_ip: str,
        server_ip: str,
        psk: str
    ) -> str:
        """Generate IPsec connection configuration"""
        config = f"conn {connection_name}\n"
        config += f"    type=tunnel\n"
        config += f"    left={server_ip}\n"
        config += f"    leftsubnet=0.0.0.0/0\n"
        config += f"    right={client_ip}\n"
        config += f"    rightsubnet=0.0.0.0/0\n"
        config += f"    authby=secret\n"
        config += f"    ike=aes256-sha256-modp2048\n"
        config += f"    esp=aes256-sha256\n"
        config += f"    keyexchange=ikev2\n"
        config += f"    auto=add\n"
        config += f"    dpdaction=restart\n"
        config += f"    dpddelay=30\n"
        config += f"    dpdtimeout=120\n"
        
        return config
    
    def add_psk_secret(self, client_ip: str, server_ip: str, psk: str):
        """Add pre-shared key secret"""
        secret_line = f"{server_ip} {client_ip} : PSK \"{psk}\"\n"
        
        with open(self.secrets_path, "a") as f:
            f.write(secret_line)
    
    def start_connection(self, connection_name: str) -> bool:
        """Start IPsec connection"""
        try:
            result = subprocess.run(
                ["ipsec", "up", connection_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error starting IPsec connection: {e}")
            return False
    
    def stop_connection(self, connection_name: str) -> bool:
        """Stop IPsec connection"""
        try:
            result = subprocess.run(
                ["ipsec", "down", connection_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error stopping IPsec connection: {e}")
            return False
    
    def get_connection_status(self, connection_name: str) -> Optional[Dict]:
        """Get IPsec connection status"""
        try:
            result = subprocess.run(
                ["ipsec", "status", connection_name],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return None
            
            return {
                'connection': connection_name,
                'status': 'active' if 'ESTABLISHED' in result.stdout else 'inactive',
                'details': result.stdout
            }
        except Exception as e:
            print(f"Error getting IPsec status: {e}")
            return None


"""
WireGuard VPN service
"""
import subprocess
import json
import os
from typing import Dict, Optional, List
from pathlib import Path
from ...utils.crypto import generate_key_pair, derive_preshared_key
from ...config import get_settings

settings = get_settings()


class WireGuardService:
    """WireGuard VPN service"""
    
    def __init__(self, interface: str = "wg0"):
        self.interface = interface
        self.config_path = Path("/etc/wireguard")
        self.config_path.mkdir(parents=True, exist_ok=True)
    
    def create_peer_config(
        self,
        client_public_key: str,
        server_public_key: str,
        server_ip: str,
        server_port: int,
        allowed_ips: List[str],
        preshared_key: Optional[str] = None
    ) -> str:
        """Generate WireGuard client configuration"""
        config = f"[Interface]\n"
        config += f"PrivateKey = <CLIENT_PRIVATE_KEY>\n"
        if preshared_key:
            config += f"PresharedKey = {preshared_key}\n"
        config += f"Address = {allowed_ips[0] if allowed_ips else '10.0.0.2/32'}\n"
        config += f"DNS = 1.1.1.1, 8.8.8.8\n\n"
        config += f"[Peer]\n"
        config += f"PublicKey = {server_public_key}\n"
        config += f"Endpoint = {server_ip}:{server_port}\n"
        config += f"AllowedIPs = {', '.join(allowed_ips)}\n"
        config += f"PersistentKeepalive = 25\n"
        
        return config
    
    def add_peer(
        self,
        client_public_key: str,
        allowed_ips: List[str],
        preshared_key: Optional[str] = None
    ) -> bool:
        """Add peer to WireGuard interface"""
        try:
            cmd = ["wg", "set", self.interface, "peer", client_public_key]
            cmd.extend(["allowed-ips", ",".join(allowed_ips)])
            
            if preshared_key:
                # Write preshared key to temp file
                psk_file = f"/tmp/wg_psk_{client_public_key[:8]}"
                with open(psk_file, "w") as f:
                    f.write(preshared_key)
                cmd.extend(["preshared-key", psk_file])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Remove temp file if created
                if preshared_key and os.path.exists(psk_file):
                    os.remove(psk_file)
                return True
            print(f"WireGuard add peer error: {result.stderr}")
            return False
        except Exception as e:
            print(f"Error adding WireGuard peer: {e}")
            return False
    
    def remove_peer(self, client_public_key: str) -> bool:
        """Remove peer from WireGuard interface"""
        try:
            result = subprocess.run(
                ["wg", "set", self.interface, "peer", client_public_key, "remove"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error removing WireGuard peer: {e}")
            return False
    
    def get_interface_status(self) -> Optional[Dict]:
        """Get WireGuard interface status"""
        try:
            result = subprocess.run(
                ["wg", "show", self.interface, "dump"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return None
            
            peers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        peers.append({
                            'public_key': parts[0],
                            'allowed_ips': parts[3].split(',') if len(parts) > 3 else [],
                            'last_handshake': parts[4] if len(parts) > 4 else None,
                            'transfer': {
                                'received': parts[5] if len(parts) > 5 else '0',
                                'sent': parts[6] if len(parts) > 6 else '0'
                            }
                        })
            
            return {
                'interface': self.interface,
                'peers': peers,
                'peer_count': len(peers)
            }
        except Exception as e:
            print(f"Error getting WireGuard status: {e}")
            return None
    
    def setup_interface(self, server_private_key: str, server_ip: str, port: int) -> bool:
        """Setup WireGuard interface"""
        try:
            # Create config file
            config_file = self.config_path / f"{self.interface}.conf"
            config = f"[Interface]\n"
            config += f"PrivateKey = {server_private_key}\n"
            config += f"Address = {server_ip}/24\n"
            config += f"ListenPort = {port}\n"
            config += f"SaveConfig = true\n"
            
            with open(config_file, "w") as f:
                f.write(config)
            
            # Bring up interface
            result = subprocess.run(
                ["wg-quick", "up", self.interface],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting up WireGuard interface: {e}")
            return False


"""
VPN Configuration Generator
"""
from typing import Dict, List, Optional
import json


class ConfigGenerator:
    """Generate VPN configurations"""
    
    @staticmethod
    def generate_wireguard_config(
        client_private_key: str,
        server_public_key: str,
        server_ip: str,
        server_port: int,
        allowed_ips: List[str],
        preshared_key: Optional[str] = None,
        dns_servers: Optional[List[str]] = None
    ) -> str:
        """Generate WireGuard client configuration"""
        config = "[Interface]\n"
        config += f"PrivateKey = {client_private_key}\n"
        
        if preshared_key:
            config += f"PresharedKey = {preshared_key}\n"
        
        # Use first allowed IP as client address
        if allowed_ips:
            client_ip = allowed_ips[0].split('/')[0] + "/32"
            config += f"Address = {client_ip}\n"
        
        if dns_servers:
            config += f"DNS = {', '.join(dns_servers)}\n"
        else:
            config += "DNS = 1.1.1.1, 8.8.8.8\n"
        
        config += "\n[Peer]\n"
        config += f"PublicKey = {server_public_key}\n"
        config += f"Endpoint = {server_ip}:{server_port}\n"
        config += f"AllowedIPs = {', '.join(allowed_ips)}\n"
        config += "PersistentKeepalive = 25\n"
        
        return config
    
    @staticmethod
    def generate_multi_hop_config(hop_configs: List[Dict]) -> str:
        """Generate multi-hop WireGuard configuration"""
        config = ""
        
        for i, hop in enumerate(hop_configs):
            config += f"[Interface_{i}]\n"
            config += f"PrivateKey = {hop['client_private_key']}\n"
            config += f"Address = {hop['client_ip']}\n"
            config += "\n"
            config += f"[Peer_{i}]\n"
            config += f"PublicKey = {hop['server_public_key']}\n"
            config += f"Endpoint = {hop['server_ip']}:{hop['server_port']}\n"
            config += f"AllowedIPs = {', '.join(hop['allowed_ips'])}\n"
            config += "\n"
        
        return config
    
    @staticmethod
    def generate_ipsec_config(
        connection_name: str,
        client_ip: str,
        server_ip: str,
        psk: str
    ) -> str:
        """Generate IPsec configuration"""
        config = f"conn {connection_name}\n"
        config += f"    type=tunnel\n"
        config += f"    left={client_ip}\n"
        config += f"    leftsubnet=0.0.0.0/0\n"
        config += f"    right={server_ip}\n"
        config += f"    rightsubnet=0.0.0.0/0\n"
        config += f"    authby=secret\n"
        config += f"    ike=aes256-sha256-modp2048\n"
        config += f"    esp=aes256-sha256\n"
        config += f"    keyexchange=ikev2\n"
        config += f"    auto=start\n"
        
        return config


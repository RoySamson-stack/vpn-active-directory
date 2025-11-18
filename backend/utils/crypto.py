"""
Cryptographic utilities for VPN
"""
import secrets
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization
from typing import Tuple


def generate_key_pair() -> Tuple[str, str]:
    """Generate WireGuard key pair (private, public)"""
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Encode in WireGuard format (base64)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    private_b64 = base64.b64encode(private_bytes).decode('ascii')
    public_b64 = base64.b64encode(public_bytes).decode('ascii')
    
    return private_b64, public_b64


def derive_preshared_key() -> str:
    """Generate preshared key for WireGuard"""
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode('ascii')


def generate_ipsec_psk() -> str:
    """Generate IPsec pre-shared key"""
    return secrets.token_hex(32)


def generate_certificate_cn() -> str:
    """Generate certificate common name"""
    return f"vpn-{secrets.token_hex(8)}"


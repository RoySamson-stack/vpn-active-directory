"""
Security utilities
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import jwt
from .crypto import generate_key_pair, derive_preshared_key

from ..config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expiration)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """Encrypt data using Fernet"""
    if key is None:
        key = settings.encryption_key
    
    # Derive key from password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'enterprise_vpn_salt',
        iterations=100000,
        backend=default_backend()
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
    f = Fernet(key_bytes)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """Decrypt data using Fernet"""
    if key is None:
        key = settings.encryption_key
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'enterprise_vpn_salt',
        iterations=100000,
        backend=default_backend()
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
    f = Fernet(key_bytes)
    decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_data.encode()))
    return decrypted.decode()


def generate_session_id() -> str:
    """Generate unique session ID"""
    return secrets.token_urlsafe(32)


def generate_audit_signature(data: str, previous_hash: Optional[str] = None) -> str:
    """Generate cryptographic signature for audit log"""
    if previous_hash:
        data = f"{previous_hash}:{data}"
    return hmac.new(
        settings.encryption_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def calculate_risk_score(session_data: dict) -> int:
    """Calculate risk score for a session (0-100)"""
    score = 0
    
    # Check if IP is in threat intel
    if session_data.get("ip_in_threat_intel"):
        score += 40
    
    # Check unusual connection time
    if session_data.get("unusual_time"):
        score += 20
    
    # Check device compliance
    if not session_data.get("device_compliant"):
        score += 30
    
    # Check engagement authorization
    if not session_data.get("engagement_authorized"):
        score += 50
    
    # Check MFA
    if not session_data.get("mfa_verified"):
        score += 25
    
    return min(score, 100)


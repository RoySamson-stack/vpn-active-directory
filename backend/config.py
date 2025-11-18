"""
Configuration management for Enterprise VPN
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Active Directory
    ad_server: str
    ad_base_dn: str
    ad_bind_user: str
    ad_bind_password: str
    ad_ssl_enabled: bool = False
    ad_ssl_verify: bool = True
    
    # RADIUS
    radius_secret: str
    radius_server: str
    radius_port: int = 1812
    
    # VPN
    vpn_domain: str
    vpn_wireguard_port: int = 51820
    vpn_ipsec_enabled: bool = True
    vpn_multi_hop_enabled: bool = True
    vpn_max_hops: int = 4
    
    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    encryption_key: str
    session_secret: str
    
    # Threat Intelligence
    threat_intel_enabled: bool = True
    virustotal_api_key: Optional[str] = None
    abuseipdb_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    audit_log_enabled: bool = True
    audit_log_encrypted: bool = True
    log_retention_days: int = 90
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    cors_origins: List[str] = []
    
    # Privacy
    traffic_obfuscation_enabled: bool = True
    decoy_traffic_enabled: bool = True
    memory_only_logs: bool = True
    
    # Monitoring
    prometheus_enabled: bool = True
    grafana_enabled: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


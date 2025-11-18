#!/usr/bin/env python3
"""
Setup Prometheus monitoring
"""
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time

# Metrics
vpn_sessions_active = Gauge('vpn_sessions_active', 'Number of active VPN sessions')
vpn_sessions_total = Counter('vpn_sessions_total', 'Total VPN sessions created', ['protocol', 'status'])
vpn_bytes_transferred = Counter('vpn_bytes_transferred', 'Bytes transferred', ['direction'])
vpn_connection_duration = Histogram('vpn_connection_duration_seconds', 'VPN connection duration')
vpn_auth_attempts = Counter('vpn_auth_attempts', 'Authentication attempts', ['result'])


def start_metrics_server(port=9091):
    """Start Prometheus metrics server"""
    start_http_server(port)
    print(f"Prometheus metrics server started on port {port}")


if __name__ == "__main__":
    start_metrics_server()


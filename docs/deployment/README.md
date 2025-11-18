# Deployment Guide

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Docker (for local development)
- PostgreSQL 15+
- Redis 7+

## Quick Start

### Docker Compose (Development)

1. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Start services:
```bash
make docker-up
```

3. Initialize database:
```bash
make init-db
```

4. Access API:
- API: http://localhost:8000
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

### Kubernetes Deployment

1. Create namespace:
```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
```

2. Update secrets:
```bash
# Edit infrastructure/kubernetes/secret.yaml with your values
kubectl apply -f infrastructure/kubernetes/secret.yaml
```

3. Deploy services:
```bash
kubectl apply -f infrastructure/kubernetes/
```

4. Check status:
```bash
kubectl get pods -n enterprise-vpn
kubectl get services -n enterprise-vpn
```

## Configuration

### Active Directory Integration

1. Set AD server details in `.env` or Kubernetes secrets
2. Ensure LDAP/RADIUS ports are accessible
3. Test connection:
```bash
python -c "from backend.services.ad_integration.ldap_client import LDAPClient; client = LDAPClient(); print(client.find_user('testuser'))"
```

### VPN Servers

Add VPN servers to database:
```python
from backend.models.server import VPNServer, ServerStatus
from backend.utils.crypto import generate_key_pair

private_key, public_key = generate_key_pair()
server = VPNServer(
    server_id="server-001",
    hostname="vpn-server-001.example.com",
    ip_address="10.0.0.1",
    public_ip="203.0.113.1",
    region="us-east-1",
    status=ServerStatus.ACTIVE,
    public_key=public_key,
    wireguard_enabled=True
)
```

## Monitoring

### Prometheus

Metrics are exposed at `/metrics` endpoint.

### Grafana

Import dashboards from `infrastructure/docker/grafana/dashboards/`

## Troubleshooting

### VPN Connection Issues

1. Check WireGuard interface:
```bash
wg show
```

2. Check logs:
```bash
kubectl logs -n enterprise-vpn deployment/vpn-api
```

3. Verify server status:
```bash
curl http://localhost:8000/api/v1/servers/
```

### Database Issues

1. Check connection:
```bash
kubectl exec -it -n enterprise-vpn postgres-0 -- psql -U vpn_user -d enterprise_vpn
```

2. Run migrations:
```bash
make init-db
```


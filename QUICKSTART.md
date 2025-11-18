# Quick Start Guide

## Enterprise VPN - Quick Start

This guide will help you get the Enterprise VPN system up and running quickly.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Kubernetes cluster (for production deployment)
- Active Directory server (for authentication)
- PostgreSQL 15+ and Redis 7+ (or use Docker Compose)

## Installation

### 1. Clone and Setup

```bash
cd enterprise-vpn-ctive-directoty
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
make install
# or
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
make init-db
# or
python scripts/deployment/init_db.py
```

### 4. Start Services

#### Option A: Docker Compose (Recommended for Development)

```bash
make docker-up
```

This starts:
- PostgreSQL database
- Redis cache
- API server
- Prometheus
- Grafana

#### Option B: Local Development

```bash
# Start PostgreSQL and Redis separately, then:
make dev
```

### 5. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Configuration

### Active Directory Setup

1. Update `.env` with your AD settings:
```env
AD_SERVER=ldap://your-ad-server:389
AD_BASE_DN=dc=example,dc=com
AD_BIND_USER=cn=admin,dc=example,dc=com
AD_BIND_PASSWORD=your_password
```

2. Test connection:
```python
from backend.services.ad_integration.ldap_client import LDAPClient
client = LDAPClient()
user = client.find_user("testuser")
print(user)
```

### Add VPN Servers

Add servers to the database:

```python
from backend.database import SessionLocal
from backend.models.server import VPNServer, ServerStatus
from backend.utils.crypto import generate_key_pair

db = SessionLocal()
private_key, public_key = generate_key_pair()

server = VPNServer(
    server_id="server-001",
    hostname="vpn-001.example.com",
    ip_address="10.0.0.1",
    public_ip="203.0.113.1",
    region="us-east-1",
    status=ServerStatus.ACTIVE,
    public_key=public_key,
    wireguard_enabled=True,
    wireguard_port=51820
)
db.add(server)
db.commit()
```

## Using the CLI Client

### Install CLI

```bash
pip install -e client/cli/
```

### Login

```bash
python client/cli/vpn_client.py login
# Enter username and password
```

### Create VPN Session

```bash
python client/cli/vpn_client.py connect --engagement-id 1 --hop-count 2
```

### List Sessions

```bash
python client/cli/vpn_client.py list
```

### Disconnect

```bash
python client/cli/vpn_client.py disconnect <session_id>
```

## Using the Web Dashboard

1. Start the frontend:
```bash
cd frontend/dashboard
npm install
npm run dev
```

2. Open http://localhost:3000

3. Login with your AD credentials

## API Usage

### Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

### Create Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_public_key": "base64_key",
    "client_ip": "203.0.113.1",
    "protocol": "wireguard",
    "hop_count": 2
  }'
```

## Kubernetes Deployment

1. Update secrets:
```bash
kubectl apply -f infrastructure/kubernetes/secret.yaml
```

2. Deploy:
```bash
make k8s-deploy
```

3. Check status:
```bash
kubectl get pods -n enterprise-vpn
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it postgres psql -U vpn_user -d enterprise_vpn

# Or for Kubernetes
kubectl exec -it -n enterprise-vpn postgres-0 -- psql -U vpn_user -d enterprise_vpn
```

### VPN Connection Issues

1. Check WireGuard status:
```bash
wg show
```

2. Check logs:
```bash
docker logs vpn-api
# Or
kubectl logs -n enterprise-vpn deployment/vpn-api
```

### Authentication Issues

1. Test LDAP connection:
```python
from backend.services.ad_integration.ldap_client import LDAPClient
client = LDAPClient()
result = client.authenticate("username", "password")
print(result)
```

## Next Steps

- Read [Architecture Documentation](docs/architecture/README.md)
- Review [API Documentation](docs/api/README.md)
- Check [Deployment Guide](docs/deployment/README.md)
- Review [Requirements](docs/enterprise-vpn-requirements.md)

## Support

For issues, check the logs and documentation. For enterprise support, contact your administrator.


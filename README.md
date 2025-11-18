# Enterprise VPN with Active Directory Integration

A robust, enterprise-grade VPN platform designed for authorized penetration testing engagements with Active Directory integration, multi-hop routing, and advanced privacy features.

## 🚀 Features

- **WireGuard & IPsec Support**: High-performance VPN protocols with automatic failover
- **Active Directory Integration**: Seamless LDAP/RADIUS authentication with MFA
- **Multi-Hop Routing**: Configurable 2-4 hop paths for enhanced privacy
- **Traffic Obfuscation**: Domain fronting, traffic shaping, and protocol blending
- **Threat Intelligence**: Automated blocking of malicious IPs and domains
- **Zero-Trust Architecture**: Policy-based access control with real-time risk scoring
- **Comprehensive Logging**: Immutable audit trails with tamper-evident signatures
- **Management Dashboard**: Web-based UI for VPN management and monitoring
- **RESTful API**: Complete API for automation and integration
- **Kubernetes Ready**: Production-ready container orchestration

## 📋 Requirements

- Kubernetes cluster (1.24+)
- Active Directory / LDAP server
- PostgreSQL database
- Redis for caching
- Minimum 4GB RAM, 2 CPU cores per node
- Docker and kubectl installed

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  VPN Gateway │────▶│  Multi-Hop  │
│  (WireGuard)│     │   (Ingress)  │     │   Relays    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Management   │
                    │    API       │
                    └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Active Dir.  │   │  Threat Intel│   │  Analytics   │
│ Integration  │   │    Service   │   │   Engine     │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
npm install --prefix frontend/dashboard

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f infrastructure/kubernetes/

# Check status
kubectl get pods -n enterprise-vpn
```

## 📚 Documentation

- [Architecture Overview](docs/architecture/README.md)
- [API Documentation](docs/api/README.md)
- [Deployment Guide](docs/deployment/README.md)
- [Requirements](docs/enterprise-vpn-requirements.md)

## 🔒 Security

- End-to-end encryption (ChaCha20Poly1305)
- Ephemeral key generation per session
- Hardware-backed key storage (TPM support)
- Secure boot and disk encryption
- Regular security audits

## 📊 Monitoring

- Prometheus metrics
- Grafana dashboards
- ELK stack for logging
- Real-time alerting

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues and questions, please open an issue or contact support.

# vpn-active-directory

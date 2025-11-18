# Architecture Documentation

## System Overview

The Enterprise VPN platform is built with a microservices architecture, designed for scalability, security, and compliance.

## Components

### 1. API Server (FastAPI)
- RESTful API for VPN management
- JWT-based authentication
- Active Directory integration
- Session management
- Threat intelligence integration

### 2. VPN Services
- **WireGuard Service**: High-performance VPN protocol
- **IPSec Service**: Legacy protocol support
- **Multi-Hop Service**: Enhanced privacy routing
- **Session Manager**: Lifecycle management

### 3. Active Directory Integration
- LDAP client for user authentication
- RADIUS support for network authentication
- Group membership checking
- User synchronization

### 4. Threat Intelligence
- AbuseIPDB integration
- VirusTotal integration (optional)
- Local threat database
- Real-time IP/domain checking

### 5. Analytics & Audit
- Immutable audit logging
- Merkle tree signatures
- Compliance reporting
- Real-time metrics

## Data Flow

```
Client → API Server → Session Manager → VPN Service → WireGuard/IPSec
                ↓
         Active Directory
                ↓
         Threat Intelligence
                ↓
         Audit Logging
```

## Security Architecture

### Authentication Flow
1. Client authenticates via AD/LDAP
2. JWT token issued
3. Token validated on each request
4. Session created with ephemeral keys

### Multi-Hop Routing
1. Client connects to ingress server
2. Traffic routed through relay servers
3. Exit via egress server
4. Each hop uses separate keys

### Privacy Features
- Ephemeral key generation
- Memory-only session logs
- Encrypted audit trails
- Traffic obfuscation

## Database Schema

### Core Tables
- `users`: User accounts synced from AD
- `vpn_sessions`: Active VPN connections
- `engagements`: Pentesting contracts
- `vpn_servers`: VPN infrastructure
- `threat_intel`: Blocked indicators
- `audit_logs`: Compliance logs

## Deployment Architecture

### Kubernetes
- Namespace: `enterprise-vpn`
- Deployment: 3 replicas
- Services: LoadBalancer for external access
- Persistent volumes for database

### Docker Compose
- Development environment
- All services in single stack
- Local networking

## Monitoring

### Metrics (Prometheus)
- Active sessions count
- Bandwidth usage
- Authentication attempts
- Connection duration

### Logging
- Structured JSON logs
- Audit trail with signatures
- Error tracking

## Scalability

### Horizontal Scaling
- API servers: Stateless, scale horizontally
- VPN servers: Add more nodes
- Database: Read replicas

### Load Balancing
- Kubernetes service load balancing
- Session affinity for VPN connections
- Health checks for availability

## High Availability

### Failover
- Multiple API replicas
- Database replication
- VPN server redundancy

### Backup
- Daily database backups
- Encrypted audit log exports
- Configuration versioning


# Hosting on Segfault

## ✅ Yes, You Can Host This on Segfault!

Segfault is a great choice for hosting this VPN platform. Here's how to set it up.

## What is Segfault?

Segfault is a VPS provider that offers:
- Affordable pricing
- Multiple locations
- Good performance
- Root access
- Docker support

## Prerequisites

1. Segfault VPS account
2. At least 2GB RAM, 2 CPU cores (4GB+ recommended)
3. Ubuntu 22.04 or Debian 12
4. Root or sudo access

## Quick Setup on Segfault

### 1. Initial Server Setup

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Install Git
apt install git -y

# Install Python and dependencies
apt install python3 python3-pip python3-venv -y
```

### 2. Clone and Setup Project

```bash
# Clone your repository
git clone <your-repo-url> enterprise-vpn
cd enterprise-vpn

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Important Segfault-specific settings:**
```env
# Use Segfault's public IP
VPN_DOMAIN=your-segfault-ip-or-domain

# Database (use Docker Compose PostgreSQL)
DATABASE_URL=postgresql://vpn_user:vpn_pass@postgres:5432/enterprise_vpn

# API (accessible from outside)
API_HOST=0.0.0.0
API_PORT=8000

# WireGuard port (make sure Segfault allows UDP)
VPN_WIREGUARD_PORT=51820
```

### 4. Configure Firewall

```bash
# Allow SSH
ufw allow 22/tcp

# Allow API
ufw allow 8000/tcp

# Allow WireGuard
ufw allow 51820/udp

# Allow IPsec (if using)
ufw allow 500/udp
ufw allow 4500/udp

# Enable firewall
ufw enable
```

### 5. Start Services with Docker Compose

```bash
cd infrastructure/docker

# Edit docker-compose.yml if needed
nano docker-compose.yml

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 6. Initialize Database

```bash
# Wait for PostgreSQL to be ready
sleep 10

# Initialize database
docker-compose exec api python scripts/deployment/init_db.py
```

### 7. Access Your VPN

- **API**: `http://your-segfault-ip:8000`
- **API Docs**: `http://your-segfault-ip:8000/docs`
- **Grafana**: `http://your-segfault-ip:3001`

## Segfault-Specific Considerations

### 1. **IP Address**
- Segfault provides a public IP
- Use this IP in your `VPN_DOMAIN` setting
- Or set up a domain name pointing to Segfault IP

### 2. **Port Restrictions**
- Some Segfault plans may restrict certain ports
- WireGuard uses UDP port 51820 (usually allowed)
- If blocked, contact Segfault support or use different port

### 3. **Resource Limits**
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- Monitor with: `docker stats`

### 4. **Storage**
- Ensure enough disk space for logs and database
- PostgreSQL data grows over time
- Set up log rotation in docker-compose.yml

### 5. **Backup Strategy**

```bash
# Create backup script
cat > /root/backup-vpn.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U vpn_user enterprise_vpn > $BACKUP_DIR/db_$DATE.sql

# Backup configs
tar -czf $BACKUP_DIR/configs_$DATE.tar.gz /etc/wireguard .env

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
EOF

chmod +x /root/backup-vpn.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup-vpn.sh") | crontab -
```

## Alternative: Direct Installation (No Docker)

If you prefer not to use Docker on Segfault:

### 1. Install System Dependencies

```bash
apt install -y \
    postgresql-15 \
    redis-server \
    wireguard \
    iptables \
    iproute2 \
    strongswan \
    python3-pip \
    python3-venv
```

### 2. Setup PostgreSQL

```bash
sudo -u postgres psql << EOF
CREATE DATABASE enterprise_vpn;
CREATE USER vpn_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE enterprise_vpn TO vpn_user;
\q
EOF
```

### 3. Configure WireGuard

```bash
# Enable IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Create WireGuard directory
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard
```

### 4. Run Application

```bash
cd /path/to/enterprise-vpn
source venv/bin/activate
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

## Production Deployment on Segfault

### 1. Use Systemd Service

```bash
cat > /etc/systemd/system/vpn-api.service << 'EOF'
[Unit]
Description=Enterprise VPN API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/enterprise-vpn
Environment="PATH=/root/enterprise-vpn/venv/bin"
ExecStart=/root/enterprise-vpn/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vpn-api
systemctl start vpn-api
```

### 2. Setup Nginx Reverse Proxy (Optional)

```bash
apt install nginx -y

cat > /etc/nginx/sites-available/vpn << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/vpn /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 3. SSL with Let's Encrypt

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

## Monitoring on Segfault

### 1. Resource Monitoring

```bash
# Install monitoring tools
apt install htop iotop -y

# Check resource usage
htop
docker stats
```

### 2. Log Monitoring

```bash
# View API logs
docker-compose logs -f api

# View system logs
journalctl -u vpn-api -f
```

## Troubleshooting on Segfault

### Port Issues
```bash
# Check if ports are open
netstat -tulpn | grep 8000
netstat -tulpn | grep 51820

# Test from outside
curl http://your-segfault-ip:8000/health
```

### Performance Issues
```bash
# Check resource usage
free -h
df -h
top

# Restart services if needed
docker-compose restart
```

### Database Issues
```bash
# Check PostgreSQL
docker-compose exec postgres psql -U vpn_user -d enterprise_vpn -c "SELECT 1;"

# Restore from backup if needed
docker-compose exec -T postgres psql -U vpn_user enterprise_vpn < backup.sql
```

## Cost Optimization on Segfault

1. **Use Docker Compose**: More efficient than separate VMs
2. **Enable Log Rotation**: Prevent disk fill-up
3. **Monitor Resource Usage**: Right-size your plan
4. **Use Redis for Caching**: Reduce database load
5. **Regular Backups**: But don't keep too many

## Security on Segfault

1. **Firewall**: UFW configured above
2. **SSH Keys**: Disable password auth
3. **Regular Updates**: `apt update && apt upgrade`
4. **Strong Passwords**: For database and services
5. **VPN Access**: Consider restricting API to VPN-only access

## Next Steps

1. ✅ Set up Segfault VPS
2. ✅ Install Docker and dependencies
3. ✅ Configure environment variables
4. ✅ Start services
5. ✅ Test API endpoints
6. ✅ Configure Active Directory
7. ✅ Add VPN servers
8. ✅ Create first engagement
9. ✅ Connect first client

## Support

If you encounter issues on Segfault:
1. Check Segfault status page
2. Review application logs
3. Verify firewall rules
4. Check resource usage
5. Review this documentation

---

**Segfault is an excellent choice for hosting this VPN platform!** It provides the flexibility, performance, and cost-effectiveness needed for a production deployment.


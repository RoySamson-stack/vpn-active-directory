#!/bin/bash
# Setup script for VPN server

set -e

echo "Setting up Enterprise VPN Server..."

# Install system dependencies
if [ -f /etc/debian_version ]; then
    apt-get update
    apt-get install -y wireguard iptables iproute2 strongswan python3-pip
elif [ -f /etc/redhat-release ]; then
    yum install -y wireguard-tools iptables iproute strongswan python3-pip
fi

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding=1" >> /etc/sysctl.conf
sysctl -p

# Create directories
mkdir -p /etc/wireguard
mkdir -p /var/log/vpn

# Set permissions
chmod 700 /etc/wireguard

echo "Server setup complete!"


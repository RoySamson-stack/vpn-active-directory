#!/usr/bin/env python3
"""
Enterprise VPN CLI Client
"""
import click
import requests
import json
import subprocess
import os
from pathlib import Path
from typing import Optional


class VPNClient:
    """VPN Client"""
    
    def __init__(self, api_url: str, token: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def login(self, username: str, password: str) -> dict:
        """Login and get access token"""
        response = self.session.post(
            f"{self.api_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        return data
    
    def create_session(
        self,
        engagement_id: Optional[int] = None,
        protocol: str = "wireguard",
        hop_count: int = 1
    ) -> dict:
        """Create VPN session"""
        # Generate client keys
        private_key, public_key = self._generate_wireguard_keys()
        
        # Get client IP
        client_ip = self._get_client_ip()
        
        response = self.session.post(
            f"{self.api_url}/api/v1/sessions/",
            json={
                "engagement_id": engagement_id,
                "client_public_key": public_key,
                "client_ip": client_ip,
                "protocol": protocol,
                "hop_count": hop_count
            }
        )
        response.raise_for_status()
        session_data = response.json()
        
        # Save config
        config = session_data.get('config', '')
        config = config.replace('<CLIENT_PRIVATE_KEY>', private_key)
        
        config_path = Path.home() / '.vpn' / f"{session_data['session_id']}.conf"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(config)
        
        return {
            **session_data,
            'config_path': str(config_path),
            'private_key': private_key
        }
    
    def list_sessions(self) -> list:
        """List VPN sessions"""
        response = self.session.get(f"{self.api_url}/api/v1/sessions/")
        response.raise_for_status()
        return response.json()
    
    def terminate_session(self, session_id: str) -> dict:
        """Terminate VPN session"""
        response = self.session.delete(f"{self.api_url}/api/v1/sessions/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def _generate_wireguard_keys(self) -> tuple:
        """Generate WireGuard key pair"""
        # Use wg command if available
        try:
            result = subprocess.run(
                ['wg', 'genkey'],
                capture_output=True,
                text=True,
                check=True
            )
            private_key = result.stdout.strip()
            
            result = subprocess.run(
                ['wg', 'pubkey'],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            )
            public_key = result.stdout.strip()
            return private_key, public_key
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to Python implementation
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            import base64
            
            private_key_obj = X25519PrivateKey.generate()
            public_key_obj = private_key_obj.public_key()
            
            private_bytes = private_key_obj.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            private_key = base64.b64encode(private_bytes).decode('ascii')
            public_key = base64.b64encode(public_bytes).decode('ascii')
            
            return private_key, public_key
    
    def _get_client_ip(self) -> str:
        """Get client public IP"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return "0.0.0.0"


@click.group()
@click.option('--api-url', default='http://localhost:8000', envvar='VPN_API_URL')
@click.pass_context
def cli(ctx, api_url):
    """Enterprise VPN CLI Client"""
    ctx.ensure_object(dict)
    ctx.obj['api_url'] = api_url
    ctx.obj['client'] = VPNClient(api_url)


@cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.pass_context
def login(ctx, username, password):
    """Login to VPN service"""
    client = ctx.obj['client']
    try:
        result = client.login(username, password)
        click.echo(f"Login successful! Token: {result['access_token'][:20]}...")
        # Save token to file
        token_file = Path.home() / '.vpn' / 'token'
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(result['access_token'])
    except Exception as e:
        click.echo(f"Login failed: {e}", err=True)


@cli.command()
@click.option('--engagement-id', type=int)
@click.option('--protocol', default='wireguard')
@click.option('--hop-count', default=1, type=int)
@click.pass_context
def connect(ctx, engagement_id, protocol, hop_count):
    """Create VPN connection"""
    client = ctx.obj['client']
    
    # Load token if available
    token_file = Path.home() / '.vpn' / 'token'
    if token_file.exists():
        client.token = token_file.read_text().strip()
        client.session.headers.update({'Authorization': f'Bearer {client.token}'})
    
    try:
        session = client.create_session(engagement_id, protocol, hop_count)
        click.echo(f"Session created: {session['session_id']}")
        click.echo(f"Config saved to: {session['config_path']}")
        click.echo(f"\nTo connect, run:")
        click.echo(f"  wg-quick up {session['config_path']}")
    except Exception as e:
        click.echo(f"Failed to create session: {e}", err=True)


@cli.command()
@click.pass_context
def list(ctx):
    """List VPN sessions"""
    client = ctx.obj['client']
    
    token_file = Path.home() / '.vpn' / 'token'
    if token_file.exists():
        client.token = token_file.read_text().strip()
        client.session.headers.update({'Authorization': f'Bearer {client.token}'})
    
    try:
        sessions = client.list_sessions()
        for session in sessions:
            click.echo(f"{session['session_id']}: {session['status']} - {session.get('protocol', 'wireguard')}")
    except Exception as e:
        click.echo(f"Failed to list sessions: {e}", err=True)


@cli.command()
@click.argument('session_id')
@click.pass_context
def disconnect(ctx, session_id):
    """Terminate VPN session"""
    client = ctx.obj['client']
    
    token_file = Path.home() / '.vpn' / 'token'
    if token_file.exists():
        client.token = token_file.read_text().strip()
        client.session.headers.update({'Authorization': f'Bearer {client.token}'})
    
    try:
        result = client.terminate_session(session_id)
        click.echo(f"Session terminated: {session_id}")
    except Exception as e:
        click.echo(f"Failed to terminate session: {e}", err=True)


if __name__ == '__main__':
    cli()


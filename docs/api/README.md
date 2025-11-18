# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/login`) require authentication via Bearer token:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/login
Login with Active Directory credentials.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password",
  "use_radius": false
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "role": "operator"
  }
}
```

### Sessions

#### POST /sessions/
Create new VPN session.

**Request:**
```json
{
  "engagement_id": 1,
  "client_public_key": "base64_key",
  "client_ip": "203.0.113.1",
  "protocol": "wireguard",
  "hop_count": 2
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "status": "active",
  "server_public_key": "base64_key",
  "preshared_key": "base64_key",
  "server_ip": "203.0.113.10",
  "server_port": 51820,
  "hop_path": [1, 2, 3],
  "config": "[Interface]..."
}
```

#### GET /sessions/
List VPN sessions.

**Query Parameters:**
- `limit` (int): Number of results (default: 50)
- `offset` (int): Pagination offset (default: 0)

#### GET /sessions/{session_id}
Get session details and statistics.

#### DELETE /sessions/{session_id}
Terminate VPN session.

### Engagements

#### POST /engagements/
Create new engagement.

#### GET /engagements/
List engagements.

#### GET /engagements/{engagement_id}
Get engagement details.

#### PATCH /engagements/{engagement_id}
Update engagement.

#### POST /engagements/{engagement_id}/approve
Approve engagement.

### Servers

#### GET /servers/
List VPN servers.

#### GET /servers/{server_id}
Get server details.

### Threat Intelligence

#### GET /threat-intel/
List threat indicators.

#### GET /threat-intel/check/{indicator}
Check if indicator is blocked.

### Analytics

#### GET /analytics/dashboard
Get dashboard statistics.

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error


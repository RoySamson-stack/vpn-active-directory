"""
Main FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import structlog

from ..config import get_settings
from ..database import init_db, close_db, get_db
from ..utils.security import verify_token
from .routes import auth, sessions, engagements, servers, users, threat_intel, analytics

settings = get_settings()
logger = structlog.get_logger()

security = HTTPBearer()


async def verify_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Initializing database")
    await init_db()
    yield
    # Shutdown
    logger.info("Closing database connections")
    await close_db()


app = FastAPI(
    title="Enterprise VPN API",
    description="Enterprise VPN with Active Directory Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(engagements.router, prefix="/api/v1/engagements", tags=["Engagements"])
app.include_router(servers.router, prefix="/api/v1/servers", tags=["Servers"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(threat_intel.router, prefix="/api/v1/threat-intel", tags=["Threat Intelligence"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Enterprise VPN API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )


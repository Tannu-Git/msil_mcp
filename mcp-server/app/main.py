"""
MSIL MCP Server - Main Application
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings


# =============================================================================
# ASGI-Level CORS Handler - Runs BEFORE FastAPI processes anything
# =============================================================================
class CORSASGIMiddleware:
    """ASGI middleware to handle CORS preflight at the lowest level."""
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            # Get origin from headers
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"*").decode("utf-8")
            
            # Build CORS response headers
            response_headers = [
                (b"access-control-allow-origin", origin.encode() if origin else b"*"),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"),
                (b"access-control-allow-headers", b"Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-API-Key, X-Requested-With, X-Correlation-ID"),
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-max-age", b"86400"),
                (b"content-length", b"0"),
                (b"content-type", b"text/plain"),
            ]
            
            # Send 200 OK response for OPTIONS
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": response_headers,
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })
            return
        
        # For non-OPTIONS requests, pass through to FastAPI
        await self.app(scope, receive, send)
from app.api import mcp, admin, chat, analytics, openapi_import, auth
from app.db.database import init_db, close_db, check_db_health, get_redis_client
from app.services.monitoring_service import monitoring_service
from app.core.auth.jwt_handler import JWTHandler
from app.core.auth import oauth2_provider as oauth2_module
from app.core.cache.service import cache_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"API Gateway Mode: {settings.API_GATEWAY_MODE}")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis Cache
    if settings.REDIS_ENABLED:
        try:
            await cache_service.connect()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            logger.warning("Continuing without Redis cache")
    
    # Initialize OAuth2 Provider
    if settings.OAUTH2_ENABLED:
        jwt_handler = JWTHandler(
            secret_key=settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expire_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        from app.core.auth.oauth2_provider import OAuth2Provider
        oauth2_module.oauth2_provider = OAuth2Provider(
            jwt_handler=jwt_handler,
            debug_mode=settings.DEBUG
        )
        logger.info("OAuth2 authentication initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("Database connections closed")
    
    if settings.REDIS_ENABLED:
        await cache_service.close()
        logger.info("Redis connection closed")


# Create FastAPI application
_fastapi_app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MSIL Composite MCP Server - AI-Powered Service Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# Monitoring Middleware
class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request monitoring and metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip monitoring for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", f"req-{time.time()}")
        request.state.correlation_id = correlation_id
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        monitoring_service.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration
        )
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s",
            extra={"correlation_id": correlation_id}
        )
        
        return response


_fastapi_app.add_middleware(MonitoringMiddleware)

# CORS Configuration
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
_fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
_fastapi_app.include_router(auth.router, prefix="/api", tags=["Authentication"])
_fastapi_app.include_router(mcp.router, tags=["MCP Protocol"])
_fastapi_app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
_fastapi_app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
_fastapi_app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
_fastapi_app.include_router(openapi_import.router, prefix="/api/admin/openapi", tags=["OpenAPI Import"])


@_fastapi_app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "mode": settings.API_GATEWAY_MODE,
        "demo_mode": settings.DEMO_MODE
    }


@_fastapi_app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    health_status = await monitoring_service.get_health_status()
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_gateway_mode": settings.API_GATEWAY_MODE,
        "demo_mode": settings.DEMO_MODE,
        "database": "connected",
        "redis": "connected",
        **health_status
    }


@_fastapi_app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes/ECS"""
    db_healthy = await check_db_health()
    
    redis_healthy = True
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_healthy = False
    
    readiness = await monitoring_service.get_readiness_status(db_healthy, redis_healthy)
    
    if readiness["status"] == "ready":
        return readiness
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=readiness)


@_fastapi_app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return monitoring_service.get_metrics()


# =============================================================================
# WRAP APP WITH ASGI CORS HANDLER - This runs BEFORE FastAPI
# =============================================================================
app = CORSASGIMiddleware(_fastapi_app)
logger.info(f"CORS ASGI Middleware enabled - DEMO_MODE={settings.DEMO_MODE}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

"""
MSIL MCP Server Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "MSIL MCP Server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://msil_mcp:msil_mcp_dev_2026@localhost:5432/msil_mcp_db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000  # Max cache entries
    
    # API Gateway Mode: "mock" or "msil_apim"
    API_GATEWAY_MODE: str = "mock"
    
    # Mock API Configuration
    MOCK_API_BASE_URL: str = "http://localhost:8080"
    
    # MSIL APIM Configuration
    MSIL_APIM_BASE_URL: str = "https://apim-dev.marutisuzuki.com"
    MSIL_APIM_SUBSCRIPTION_KEY: Optional[str] = None
    MSIL_APIM_CLIENT_ID: Optional[str] = None
    MSIL_APIM_CLIENT_SECRET: Optional[str] = None
    MSIL_APIM_TENANT_ID: Optional[str] = None
    
    # Dedicated APIM Subscription for MCP (P1-4)
    APIM_MCP_SUBSCRIPTION_KEY: Optional[str] = None
    APIM_MCP_SUBSCRIPTION_NAME: str = "mcp-channel"
    APIM_PROPAGATE_USER_CONTEXT: bool = True
    APIM_USER_CONTEXT_HEADER: str = "X-User-Context"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4096
    
    # Security
    API_KEY: str = "msil-mcp-dev-key-2026"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:5174"
    
    # OAuth2/JWT Authentication
    OAUTH2_ENABLED: bool = True
    JWT_SECRET: str = "msil-mcp-jwt-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OIDC Configuration (P0-1)
    OIDC_ENABLED: bool = False
    OIDC_ISSUER: Optional[str] = None
    OIDC_AUDIENCE: Optional[str] = None
    OIDC_JWKS_URL: Optional[str] = None
    OIDC_REQUIRED_SCOPES: str = "openid,profile,email"
    OIDC_JWKS_CACHE_TTL: int = 3600
    TOKEN_VALIDATE_ISSUER: bool = True
    TOKEN_VALIDATE_AUDIENCE: bool = True
    TOKEN_VALIDATE_NONCE: bool = True
    
    # OPA Policy Engine
    OPA_ENABLED: bool = True
    OPA_URL: str = "http://localhost:8181"
    
    # Audit Service
    AUDIT_ENABLED: bool = True
    AUDIT_S3_BUCKET: Optional[str] = None
    AUDIT_RETENTION_DAYS: int = 365  # 12 months
    
    # S3 WORM Audit Storage (P0-4)
    AUDIT_S3_ENABLED: bool = False
    AUDIT_S3_REGION: str = "ap-south-1"
    AUDIT_S3_OBJECT_LOCK_MODE: str = "GOVERNANCE"
    AUDIT_S3_RETENTION_DAYS: int = 365
    AUDIT_DUAL_WRITE: bool = True
    
    # Resilience
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_EXPONENTIAL_BASE: int = 2  # seconds
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_USER: int = 100  # requests per minute
    RATE_LIMIT_PER_TOOL: int = 50   # requests per minute
    
    # Idempotency (P0-2)
    IDEMPOTENCY_ENABLED: bool = True
    IDEMPOTENCY_REQUIRED: bool = False
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    IDEMPOTENCY_STORE_TYPE: str = "redis"
    
    # PIM/PAM Configuration (P0-3)
    PIM_ENABLED: bool = False
    PIM_PROVIDER: str = "local"
    PAM_ENDPOINT: Optional[str] = None
    ELEVATION_DURATION_SECONDS: int = 3600
    ELEVATION_REQUIRE_REASON: bool = True
    ELEVATION_REQUIRE_APPROVAL: bool = False
    
    # Batch Execution
    BATCH_MAX_CONCURRENCY: int = 10
    BATCH_MAX_SIZE: int = 20  # Maximum tools per batch
    
    # WAF Configuration (P1-1)
    WAF_ENABLED: bool = False
    WAF_WEB_ACL_ARN: Optional[str] = None
    WAF_RATE_LIMIT: int = 2000
    WAF_IP_ALLOWLIST_ENABLED: bool = False
    WAF_ALLOWED_IPS: str = ""  # Comma-separated CIDRs
    
    # mTLS Configuration (P1-2)
    MTLS_ENABLED: bool = False
    MTLS_CA_CERT_PATH: str = "/certs/ca.crt"
    MTLS_CLIENT_CERT_PATH: str = "/certs/client.crt"
    MTLS_CLIENT_KEY_PATH: str = "/certs/client.key"
    MTLS_SERVER_CERT_PATH: Optional[str] = "/certs/server.crt"
    MTLS_SERVER_KEY_PATH: Optional[str] = "/certs/server.key"
    MTLS_VERIFY_MODE: str = "CERT_REQUIRED"
    MTLS_MIN_TLS_VERSION: str = "TLSv1_2"
    
    # Tool Risk Management (P1-3)
    TOOL_RISK_ENFORCEMENT_ENABLED: bool = True
    TOOL_RISK_DEFAULT_LEVEL: str = "read"
    
    # Container Security (P2)
    CONTAINER_HARDENING_ENABLED: bool = True
    CONTAINER_USER_UID: int = 1000
    CONTAINER_USER_GID: int = 1000
    CONTAINER_READONLY_ROOT: bool = True
    CONTAINER_DROP_ALL_CAPS: bool = True
    CONTAINER_NO_NEW_PRIVILEGES: bool = True
    
    # Security Testing (P2)
    SECURITY_TESTS_ENABLED: bool = True
    SECURITY_SCAN_ON_STARTUP: bool = False
    SECURITY_SCAN_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    
    # Network Policies (P2)
    NETWORK_POLICIES_ENABLED: bool = True
    NETWORK_DENY_BY_DEFAULT: bool = True
    NETWORK_ALLOWED_NAMESPACES: str = "mcp-production,kube-system"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

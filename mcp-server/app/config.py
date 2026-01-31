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
    CACHE_TTL: int = 300  # 5 minutes
    
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
    
    # OPA Policy Engine
    OPA_ENABLED: bool = True
    OPA_URL: str = "http://localhost:8181"
    
    # Audit Service
    AUDIT_ENABLED: bool = True
    AUDIT_S3_BUCKET: Optional[str] = None
    AUDIT_RETENTION_DAYS: int = 365  # 12 months
    
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

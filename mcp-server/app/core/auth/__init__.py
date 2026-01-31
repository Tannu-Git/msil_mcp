"""Authentication module for MSIL MCP Server.

Provides OAuth2/OIDC authentication with JWT token validation.
"""

from .jwt_handler import JWTHandler
from .oauth2_provider import OAuth2Provider, get_current_user
from .models import TokenData, UserInfo

__all__ = [
    "JWTHandler",
    "OAuth2Provider",
    "get_current_user",
    "TokenData",
    "UserInfo",
]

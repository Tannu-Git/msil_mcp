"""Authentication models for MSIL MCP Server."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TokenData:
    """JWT token payload data."""
    
    user_id: str
    email: str
    roles: List[str]
    exp: datetime
    iat: datetime
    sub: str


@dataclass
class UserInfo:
    """User information from authentication."""
    
    user_id: str
    email: str
    name: Optional[str]
    roles: List[str]
    is_active: bool = True
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return "admin" in self.roles


@dataclass
class LoginRequest:
    """Login request model."""
    
    email: str
    password: str


@dataclass
class TokenResponse:
    """Token response model."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None

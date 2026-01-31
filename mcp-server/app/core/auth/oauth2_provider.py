"""OAuth2 provider and authentication dependencies."""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_handler import JWTHandler
from .models import UserInfo, TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


class OAuth2Provider:
    """OAuth2 provider for handling authentication."""
    
    def __init__(
        self,
        jwt_handler: JWTHandler,
        debug_mode: bool = False
    ):
        """Initialize OAuth2 provider.
        
        Args:
            jwt_handler: JWT token handler instance
            debug_mode: If True, allows bypassing auth for testing
        """
        self.jwt_handler = jwt_handler
        self.debug_mode = debug_mode
        
        # In-memory user store for demo (replace with database in production)
        self.users = {
            "admin@msil.com": {
                "user_id": "usr_admin_001",
                "email": "admin@msil.com",
                "password_hash": "admin123",  # In production, use bcrypt
                "name": "MSIL Admin",
                "roles": ["admin", "developer", "operator"],
                "is_active": True
            },
            "developer@msil.com": {
                "user_id": "usr_dev_001",
                "email": "developer@msil.com",
                "password_hash": "dev123",
                "name": "MSIL Developer",
                "roles": ["developer", "operator"],
                "is_active": True
            },
            "operator@msil.com": {
                "user_id": "usr_op_001",
                "email": "operator@msil.com",
                "password_hash": "op123",
                "name": "MSIL Operator",
                "roles": ["operator"],
                "is_active": True
            }
        }
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInfo]:
        """Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            UserInfo if authentication successful, None otherwise
        """
        user_data = self.users.get(email)
        
        if not user_data:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        
        # In production, use bcrypt.checkpw()
        if user_data["password_hash"] != password:
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        
        if not user_data["is_active"]:
            logger.warning(f"Authentication failed: User inactive - {email}")
            return None
        
        logger.info(f"User authenticated successfully: {email}")
        
        return UserInfo(
            user_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data["name"],
            roles=user_data["roles"],
            is_active=user_data["is_active"]
        )
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserInfo:
        """Get current user from JWT token.
        
        Args:
            credentials: HTTP authorization credentials with Bearer token
            
        Returns:
            UserInfo for authenticated user
            
        Raises:
            HTTPException: If authentication fails
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Extract token from Authorization header
            token = credentials.credentials
            
            # Verify and decode token
            payload = self.jwt_handler.verify_token(token)
            
            # Extract user information
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            roles: list = payload.get("roles", [])
            
            if user_id is None or email is None:
                logger.warning("Invalid token payload: missing user_id or email")
                raise credentials_exception
            
            # Create UserInfo from token
            user_info = UserInfo(
                user_id=user_id,
                email=email,
                name=payload.get("name"),
                roles=roles,
                is_active=True
            )
            
            return user_info
            
        except ValueError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Unexpected error in authentication: {str(e)}")
            raise credentials_exception
    
    async def get_optional_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[UserInfo]:
        """Get current user optionally (for endpoints that support both auth and unauth).
        
        Args:
            credentials: HTTP authorization credentials with Bearer token
            
        Returns:
            UserInfo if authenticated, None otherwise
        """
        if not credentials:
            return None
        
        try:
            return await self.get_current_user(credentials)
        except HTTPException:
            return None


# Global OAuth2 provider instance (will be initialized in main.py)
oauth2_provider: Optional[OAuth2Provider] = None


def get_oauth2_provider() -> OAuth2Provider:
    """Get global OAuth2 provider instance."""
    if oauth2_provider is None:
        # If not initialized, log error and raise HTTP exception
        logger.error("OAuth2Provider not initialized - check server startup")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="Authentication service not initialized"
        )
    return oauth2_provider


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    """Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        UserInfo for authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    provider = get_oauth2_provider()
    return await provider.get_current_user(credentials)


async def get_current_active_user(
    current_user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Dependency to get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        UserInfo if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_role(required_role: str):
    """Dependency factory to require specific role.
    
    Args:
        required_role: Role required to access endpoint
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return role_checker


async def require_admin(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Dependency to require admin role.
    
    Args:
        current_user: Current user from token
        
    Returns:
        UserInfo if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

"""Authentication API endpoints."""

import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.auth.oauth2_provider import OAuth2Provider, get_oauth2_provider, get_current_user
from app.core.auth.models import UserInfo, TokenResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    provider: OAuth2Provider = Depends(get_oauth2_provider)
) -> TokenResponse:
    """Authenticate user and return JWT tokens.
    
    Args:
        request: Login credentials
        provider: OAuth2 provider instance
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = await provider.authenticate_user(request.email, request.password)
    
    if not user:
        logger.warning(f"Login failed for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token data
    token_data = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles
    }
    
    # Generate tokens
    access_token = provider.jwt_handler.create_access_token(token_data)
    refresh_token = provider.jwt_handler.create_refresh_token({"sub": user.user_id})
    
    logger.info(f"User logged in successfully: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    provider: OAuth2Provider = Depends(get_oauth2_provider)
) -> TokenResponse:
    """Refresh access token using refresh token.
    
    Args:
        request: Refresh token
        provider: OAuth2 provider instance
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Verify refresh token
        payload = provider.jwt_handler.verify_token(request.refresh_token)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Find user (in production, query from database)
        user = None
        for user_data in provider.users.values():
            if user_data["user_id"] == user_id:
                user = UserInfo(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    name=user_data["name"],
                    roles=user_data["roles"],
                    is_active=user_data["is_active"]
                )
                break
        
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Create new access token
        token_data = {
            "sub": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": user.roles
        }
        
        access_token = provider.jwt_handler.create_access_token(token_data)
        
        logger.info(f"Access token refreshed for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except ValueError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=Dict)
async def get_current_user_info(
    current_user: UserInfo = Depends(get_current_user)
) -> Dict:
    """Get current authenticated user information.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        User information
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "roles": current_user.roles,
        "is_active": current_user.is_active
    }


@router.post("/logout")
async def logout(
    current_user: UserInfo = Depends(get_current_user)
) -> Dict:
    """Logout current user.
    
    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token. In production, you might want to add token to a blacklist.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}

"""JWT token handler for authentication."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from jose import JWTError, jwt

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handler for JWT token creation and validation."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7
    ):
        """Initialize JWT handler.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (HS256, RS256, etc.)
            access_token_expire_minutes: Access token expiry in minutes
            refresh_token_expire_days: Refresh token expiry in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self,
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise
    
    def create_refresh_token(self, data: Dict) -> str:
        """Create JWT refresh token.
        
        Args:
            data: Data to encode in token
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token hasn't expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise ValueError("Token has expired")
            
            logger.debug(f"Token verified for user: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise ValueError(f"Token verification failed: {str(e)}")
    
    def decode_token_without_verification(self, token: str) -> Dict:
        """Decode token without verification (for debugging).
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}")
            return {}

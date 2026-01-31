"""OIDC-compliant JWT token validator with JWKS support."""
from jose import jwt, jwk
from typing import Dict, List, Optional
import logging
from .jwks_client import JWKSClient

logger = logging.getLogger(__name__)


class OIDCTokenValidator:
    """Validates JWT tokens according to OIDC specification."""
    
    def __init__(
        self,
        jwks_client: JWKSClient,
        issuer: str,
        audience: str,
        required_scopes: Optional[List[str]] = None
    ):
        """
        Initialize OIDC token validator.
        
        Args:
            jwks_client: JWKS client for fetching signing keys
            issuer: Expected token issuer (iss claim)
            audience: Expected token audience (aud claim)
            required_scopes: List of required scopes (optional)
        """
        self.jwks_client = jwks_client
        self.issuer = issuer
        self.audience = audience
        self.required_scopes = required_scopes or []
    
    async def validate_token(self, token: str) -> Dict:
        """
        Validate JWT token with full OIDC compliance.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload (claims)
            
        Raises:
            ValueError: If token validation fails
            jwt.JWTError: If token signature/claims are invalid
        """
        # 1. Decode header to get kid (key ID)
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise ValueError("Token missing 'kid' (key ID) in header")
            
            logger.debug(f"Token header: alg={unverified_header.get('alg')}, kid={kid}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {e}")
            raise ValueError(f"Invalid token header: {e}")
        
        # 2. Get signing key from JWKS
        try:
            signing_key_data = await self.jwks_client.get_signing_key(kid)
            public_key = jwk.construct(signing_key_data)
        except Exception as e:
            logger.error(f"Failed to get signing key for kid={kid}: {e}")
            raise ValueError(f"Failed to get signing key: {e}")
        
        # 3. Verify and decode token with all OIDC validations
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require_exp": True,
                    "require_iat": True,
                }
            )
            logger.debug(f"Token decoded successfully: sub={payload.get('sub')}, exp={payload.get('exp')}")
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise ValueError("Token has expired")
        except jwt.JWTClaimsError as e:
            logger.warning(f"Token claims validation failed: {e}")
            raise ValueError(f"Token claims invalid: {e}")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise ValueError(f"Token validation failed: {e}")
        
        # 4. Validate required scopes
        if self.required_scopes:
            token_scopes = self._extract_scopes(payload)
            missing_scopes = [s for s in self.required_scopes if s not in token_scopes]
            
            if missing_scopes:
                logger.warning(f"Token missing required scopes: {missing_scopes}")
                raise ValueError(f"Missing required scopes: {', '.join(missing_scopes)}")
            
            logger.debug(f"Token has all required scopes: {self.required_scopes}")
        
        # 5. Log nonce if present (for anti-replay tracking)
        if "nonce" in payload:
            logger.info(f"Token nonce: {payload['nonce']}")
            # TODO: Implement nonce validation against cache/store
        
        logger.info(f"Token validated successfully for subject: {payload.get('sub')}")
        return payload
    
    def _extract_scopes(self, payload: Dict) -> List[str]:
        """
        Extract scopes from token payload.
        
        Scopes can be in 'scope' (space-separated string) or 'scopes' (array).
        """
        # Check for 'scope' claim (OpenID Connect standard)
        if "scope" in payload:
            scope_str = payload["scope"]
            if isinstance(scope_str, str):
                return scope_str.split()
            elif isinstance(scope_str, list):
                return scope_str
        
        # Check for 'scopes' claim (some providers use this)
        if "scopes" in payload:
            scopes = payload["scopes"]
            if isinstance(scopes, list):
                return scopes
            elif isinstance(scopes, str):
                return scopes.split()
        
        # Check for 'scp' claim (Azure AD uses this)
        if "scp" in payload:
            scp_str = payload["scp"]
            if isinstance(scp_str, str):
                return scp_str.split()
        
        logger.debug("No scopes found in token")
        return []
    
    async def validate_and_extract_user(self, token: str) -> Dict:
        """
        Validate token and extract user information.
        
        Returns:
            Dictionary with user_id, email, name, roles, scopes
        """
        payload = await self.validate_token(token)
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "preferred_username": payload.get("preferred_username"),
            "roles": payload.get("roles", []),
            "scopes": self._extract_scopes(payload),
            "token_claims": payload
        }

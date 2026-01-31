"""Elevation checker for privileged access management."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import logging
from .models import ElevationStatus, ElevationRequest

logger = logging.getLogger(__name__)


class ElevationChecker:
    """Check if user has elevated privileges for privileged operations."""
    
    def __init__(
        self,
        pam_endpoint: Optional[str] = None,
        elevation_duration: int = 3600,  # 1 hour default
        provider: str = "local"
    ):
        """
        Initialize elevation checker.
        
        Args:
            pam_endpoint: Optional PAM system endpoint for external validation
            elevation_duration: Duration of elevation in seconds
            provider: PIM/PAM provider (local, azure_pim, cyberark, okta)
        """
        self.pam_endpoint = pam_endpoint
        self.elevation_duration = elevation_duration
        self.provider = provider
        self._cache: Dict[str, ElevationStatus] = {}
    
    async def is_user_elevated(
        self,
        user_id: str,
        tool_name: str,
        token_claims: Dict[str, Any]
    ) -> bool:
        """
        Check if user has current elevation.
        
        Args:
            user_id: User identifier
            tool_name: Tool name requesting elevation
            token_claims: JWT token claims
            
        Returns:
            True if user is elevated, False otherwise
        """
        # Method 1: Check JWT claims for elevation
        elevation_status = self._check_token_elevation(token_claims)
        if elevation_status and elevation_status.is_valid:
            logger.info(f"User {user_id} is elevated via token for {tool_name}")
            return True
        
        # Method 2: Check with external PAM system
        if self.pam_endpoint and self.provider != "local":
            is_elevated = await self._check_pam_elevation(user_id, tool_name)
            if is_elevated:
                logger.info(f"User {user_id} is elevated via PAM for {tool_name}")
                return True
        
        # Method 3: Check local cache (for demo mode)
        cache_key = f"{user_id}:{tool_name}"
        if cache_key in self._cache:
            status = self._cache[cache_key]
            if status.is_valid:
                logger.info(f"User {user_id} is elevated via cache for {tool_name}")
                return True
            else:
                # Remove expired elevation
                del self._cache[cache_key]
        
        logger.info(f"User {user_id} is NOT elevated for {tool_name}")
        return False
    
    def _check_token_elevation(self, token_claims: Dict[str, Any]) -> Optional[ElevationStatus]:
        """
        Check elevation from JWT token claims.
        
        Expected claim format:
        {
            "elevation_status": {
                "elevated": true,
                "elevated_at": "2026-01-31T10:00:00Z",
                "expires_at": "2026-01-31T11:00:00Z",
                "reason": "Service booking approval"
            }
        }
        """
        elevation_claim = token_claims.get("elevation_status")
        if not elevation_claim:
            return None
        
        try:
            elevated_at = None
            expires_at = None
            
            if "elevated_at" in elevation_claim:
                elevated_at = datetime.fromisoformat(
                    elevation_claim["elevated_at"].replace("Z", "+00:00")
                )
            
            if "expires_at" in elevation_claim:
                expires_at = datetime.fromisoformat(
                    elevation_claim["expires_at"].replace("Z", "+00:00")
                )
            
            return ElevationStatus(
                elevated=elevation_claim.get("elevated", False),
                elevated_at=elevated_at,
                expires_at=expires_at,
                reason=elevation_claim.get("reason"),
                approved_by=elevation_claim.get("approved_by")
            )
        except Exception as e:
            logger.error(f"Failed to parse elevation claim: {e}")
            return None
    
    async def _check_pam_elevation(
        self,
        user_id: str,
        tool_name: str
    ) -> bool:
        """
        Check elevation with external PAM system.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            True if elevated, False otherwise
        """
        if not self.pam_endpoint:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.pam_endpoint}/check-elevation",
                    json={
                        "user_id": user_id,
                        "resource": tool_name,
                        "action": "execute"
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("elevated", False)
        except httpx.TimeoutException:
            logger.error("PAM elevation check timed out")
            return False
        except Exception as e:
            logger.error(f"PAM elevation check failed: {e}")
            return False
    
    async def request_elevation(
        self,
        user_id: str,
        tool_name: str,
        reason: str,
        requires_approval: bool = False
    ) -> ElevationRequest:
        """
        Request elevation (just-in-time access).
        
        Args:
            user_id: User identifier
            tool_name: Tool requesting elevation
            reason: Reason for elevation
            requires_approval: Whether approval is required
            
        Returns:
            ElevationRequest with status and approval URL if needed
        """
        request = ElevationRequest(
            user_id=user_id,
            tool_name=tool_name,
            reason=reason,
            requested_at=datetime.utcnow(),
            requires_approval=requires_approval
        )
        
        if self.pam_endpoint and self.provider != "local":
            # Request elevation from PAM system
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.pam_endpoint}/request-elevation",
                        json={
                            "user_id": user_id,
                            "resource": tool_name,
                            "reason": reason,
                            "duration_seconds": self.elevation_duration
                        },
                        timeout=10.0
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("requires_approval"):
                        request.approval_url = result.get("approval_url")
                    else:
                        # Auto-approved, cache the elevation
                        self._grant_elevation_local(user_id, tool_name, reason)
            except Exception as e:
                logger.error(f"Failed to request elevation from PAM: {e}")
        else:
            # Local mode - auto-approve
            self._grant_elevation_local(user_id, tool_name, reason)
        
        return request
    
    def _grant_elevation_local(
        self,
        user_id: str,
        tool_name: str,
        reason: str
    ):
        """Grant elevation locally (for demo/local mode)."""
        cache_key = f"{user_id}:{tool_name}"
        elevated_at = datetime.utcnow()
        expires_at = elevated_at + timedelta(seconds=self.elevation_duration)
        
        self._cache[cache_key] = ElevationStatus(
            elevated=True,
            elevated_at=elevated_at,
            expires_at=expires_at,
            reason=reason,
            approved_by="auto"
        )
        
        logger.info(f"Granted local elevation to {user_id} for {tool_name} until {expires_at}")
    
    def revoke_elevation(self, user_id: str, tool_name: str):
        """Revoke elevation for user and tool."""
        cache_key = f"{user_id}:{tool_name}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Revoked elevation for {user_id} on {tool_name}")
    
    def clear_cache(self):
        """Clear all cached elevations."""
        self._cache.clear()
        logger.info("Cleared all elevation cache")

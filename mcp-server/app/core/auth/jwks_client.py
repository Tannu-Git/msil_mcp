"""JWKS Client for fetching and caching JSON Web Key Sets from IdP."""
import httpx
import time
from jose import jwk
from typing import Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class JWKSClient:
    """Client for fetching and caching JWKS from IdP."""
    
    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        """
        Initialize JWKS client.
        
        Args:
            jwks_url: URL to fetch JWKS from (e.g., https://issuer/.well-known/jwks.json)
            cache_ttl: Time to live for cached JWKS in seconds (default: 1 hour)
        """
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict] = None
        self._cache_time: float = 0
    
    async def get_signing_key(self, kid: str) -> Dict:
        """
        Get signing key for given kid (key ID).
        
        Args:
            kid: Key ID from JWT header
            
        Returns:
            JWK (JSON Web Key) dictionary
            
        Raises:
            ValueError: If key not found in JWKS
            httpx.HTTPError: If JWKS fetch fails
        """
        if self._is_cache_valid():
            return self._get_key_from_cache(kid)
        
        await self._refresh_cache()
        return self._get_key_from_cache(kid)
    
    async def _refresh_cache(self):
        """Fetch JWKS from IdP and update cache."""
        try:
            logger.info(f"Fetching JWKS from {self.jwks_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                self._cache = response.json()
                self._cache_time = time.time()
                logger.info(f"JWKS cache refreshed, found {len(self._cache.get('keys', []))} keys")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache:
            return False
        age = time.time() - self._cache_time
        is_valid = age < self.cache_ttl
        if not is_valid:
            logger.debug(f"JWKS cache expired (age: {age}s, ttl: {self.cache_ttl}s)")
        return is_valid
    
    def _get_key_from_cache(self, kid: str) -> Dict:
        """Extract key from cached JWKS."""
        if not self._cache:
            raise ValueError("JWKS cache is empty")
        
        for key in self._cache.get("keys", []):
            if key.get("kid") == kid:
                logger.debug(f"Found key with kid={kid} in cache")
                return key
        
        available_kids = [k.get("kid") for k in self._cache.get("keys", [])]
        raise ValueError(f"Key with kid={kid} not found in JWKS. Available kids: {available_kids}")
    
    def clear_cache(self):
        """Clear JWKS cache (useful for testing or forced refresh)."""
        logger.info("Clearing JWKS cache")
        self._cache = None
        self._cache_time = 0

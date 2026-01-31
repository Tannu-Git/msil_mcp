"""
Rate Limiter - Token bucket algorithm using Redis
"""
import time
import logging
from typing import Optional
from dataclasses import dataclass

from app.core.cache.service import cache_service

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information"""
    allowed: bool
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None


class RateLimiter:
    """
    Token bucket rate limiter using Redis
    
    Features:
    - Per-user rate limiting
    - Per-tool rate limiting
    - Configurable limits and windows
    """
    
    def __init__(self):
        self.cache = cache_service
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> RateLimitInfo:
        """
        Check if request is within rate limit
        
        Args:
            key: Rate limit key (e.g., "user:123" or "tool:get_dealers")
            limit: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            RateLimitInfo with decision and metadata
        """
        cache_key = f"ratelimit:{key}"
        current_time = int(time.time())
        window_start = current_time - window
        
        try:
            # Get current count
            count = await self.cache.increment(cache_key, 1, window)
            
            if count <= limit:
                return RateLimitInfo(
                    allowed=True,
                    remaining=limit - count,
                    reset_at=current_time + window
                )
            else:
                # Rate limit exceeded
                retry_after = window - (current_time % window)
                return RateLimitInfo(
                    allowed=False,
                    remaining=0,
                    reset_at=current_time + retry_after,
                    retry_after=retry_after
                )
        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitInfo(
                allowed=True,
                remaining=limit,
                reset_at=current_time + window
            )
    
    async def check_user_rate_limit(
        self,
        user_id: str,
        limit: int = 100,
        window: int = 60
    ) -> RateLimitInfo:
        """Check per-user rate limit (default: 100 req/min)"""
        return await self.check_rate_limit(f"user:{user_id}", limit, window)
    
    async def check_tool_rate_limit(
        self,
        tool_name: str,
        limit: int = 50,
        window: int = 60
    ) -> RateLimitInfo:
        """Check per-tool rate limit (default: 50 req/min)"""
        return await self.check_rate_limit(f"tool:{tool_name}", limit, window)
    
    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a key"""
        cache_key = f"ratelimit:{key}"
        return await self.cache.delete(cache_key)


# Singleton instance
rate_limiter = RateLimiter()

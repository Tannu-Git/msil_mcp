"""
Redis Cache Service - Caching and session management
"""
import json
import logging
from typing import Any, Optional, Dict
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for API responses and session data"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None
        self._enabled = settings.REDIS_ENABLED
    
    async def connect(self):
        """Initialize Redis connection"""
        if not self._enabled:
            logger.warning("Redis is disabled, using in-memory fallback")
            return
        
        try:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Falling back to in-memory cache")
            self._redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._redis:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful
        """
        if not self._redis:
            return False
        
        try:
            json_value = json.dumps(value)
            await self._redis.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._redis:
            return False
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> int:
        """
        Increment counter (useful for rate limiting)
        
        Args:
            key: Counter key
            amount: Increment amount
            ttl: Set TTL if key doesn't exist
            
        Returns:
            New counter value
        """
        if not self._redis:
            return 0
        
        try:
            # Increment counter
            new_value = await self._redis.incrby(key, amount)
            
            # Set TTL if this is first increment
            if new_value == amount and ttl:
                await self._redis.expire(key, ttl)
            
            return new_value
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple keys at once"""
        if not self._redis or not keys:
            return {}
        
        try:
            values = await self._redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: int = 300
    ) -> bool:
        """Set multiple keys at once"""
        if not self._redis or not mapping:
            return False
        
        try:
            # Convert values to JSON
            json_mapping = {
                key: json.dumps(value) 
                for key, value in mapping.items()
            }
            
            # Set all keys
            await self._redis.mset(json_mapping)
            
            # Set TTL for each key
            if ttl:
                for key in mapping.keys():
                    await self._redis.expire(key, ttl)
            
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self._redis:
            return 0
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for {pattern}: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")


# Singleton instance
cache_service = CacheService()

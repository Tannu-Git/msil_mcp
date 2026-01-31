"""Idempotency key storage with Redis backend."""
import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class IdempotencyStore:
    """Store for idempotency keys with Redis backend."""
    
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 86400):
        """
        Initialize idempotency store.
        
        Args:
            redis_client: Redis client instance
            ttl_seconds: Time to live for cached responses (default: 24 hours)
        """
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    def _make_key(self, idempotency_key: str, user_id: str) -> str:
        """
        Create namespaced key for Redis.
        
        Args:
            idempotency_key: Idempotency key from client
            user_id: User identifier
            
        Returns:
            Namespaced Redis key
        """
        return f"idempotency:{user_id}:{idempotency_key}"
    
    async def get_response(
        self,
        idempotency_key: str,
        user_id: str
    ) -> Optional[Dict[Any, Any]]:
        """
        Get cached response for idempotency key.
        
        Args:
            idempotency_key: Idempotency key to check
            user_id: User identifier
            
        Returns:
            Cached response dictionary or None if not found
        """
        key = self._make_key(idempotency_key, user_id)
        try:
            data = await self.redis.get(key)
            
            if data:
                logger.info(f"Cache hit for idempotency key: {idempotency_key[:8]}...")
                return json.loads(data)
            
            logger.debug(f"Cache miss for idempotency key: {idempotency_key[:8]}...")
            return None
        except Exception as e:
            logger.error(f"Error retrieving idempotency response: {e}")
            return None
    
    async def store_response(
        self,
        idempotency_key: str,
        user_id: str,
        response: Dict[Any, Any]
    ):
        """
        Store response with idempotency key.
        
        Args:
            idempotency_key: Idempotency key from client
            user_id: User identifier
            response: Response data to cache
        """
        key = self._make_key(idempotency_key, user_id)
        try:
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(response)
            )
            logger.info(f"Stored response for idempotency key: {idempotency_key[:8]}... (TTL: {self.ttl}s)")
        except Exception as e:
            logger.error(f"Error storing idempotency response: {e}")
            # Don't raise - idempotency is best-effort
    
    def generate_key(self, request_data: Dict) -> str:
        """
        Generate idempotency key from request data.
        
        This creates a deterministic key based on request payload,
        useful when clients don't provide explicit keys.
        
        Args:
            request_data: Request data dictionary
            
        Returns:
            SHA-256 hash of request data
        """
        # Sort keys for consistent hashing
        data_str = json.dumps(request_data, sort_keys=True)
        hash_value = hashlib.sha256(data_str.encode()).hexdigest()
        logger.debug(f"Generated idempotency key: {hash_value[:8]}...")
        return hash_value
    
    async def delete_key(self, idempotency_key: str, user_id: str):
        """
        Delete idempotency key (for testing or manual cleanup).
        
        Args:
            idempotency_key: Idempotency key to delete
            user_id: User identifier
        """
        key = self._make_key(idempotency_key, user_id)
        try:
            await self.redis.delete(key)
            logger.info(f"Deleted idempotency key: {idempotency_key[:8]}...")
        except Exception as e:
            logger.error(f"Error deleting idempotency key: {e}")
    
    async def check_exists(self, idempotency_key: str, user_id: str) -> bool:
        """
        Check if idempotency key exists without retrieving value.
        
        Args:
            idempotency_key: Idempotency key to check
            user_id: User identifier
            
        Returns:
            True if key exists, False otherwise
        """
        key = self._make_key(idempotency_key, user_id)
        try:
            exists = await self.redis.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Error checking idempotency key existence: {e}")
            return False

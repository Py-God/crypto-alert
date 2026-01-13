# src/cache/redis_client.py
import redis.asyncio as redis
from typing import Optional
import structlog

from src.config import settings

logger = structlog.get_logger()


class RedisClient:
    """Async Redis client wrapper"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis.ping()
            self._connected = True
            logger.info("redis_connected", url=settings.REDIS_URL)
        except Exception as e:
            self._connected = False
            logger.error("redis_connection_failed", error=str(e))
            # Don't raise - allow app to work without Redis
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self._connected:
            return None
        
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: str) -> bool:
        """Set key-value pair"""
        if not self._connected:
            return False
        
        try:
            await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            return False
    
    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set key-value pair with expiration"""
        if not self._connected:
            return False
        
        try:
            await self.redis.setex(key, seconds, value)
            return True
        except Exception as e:
            logger.error("redis_setex_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self._connected:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("redis_delete_error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error("redis_exists_error", key=key, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL (time to live) for a key"""
        if not self._connected:
            return -2
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error("redis_ttl_error", key=key, error=str(e))
            return -2
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected


# Global Redis client instance
redis_client = RedisClient()
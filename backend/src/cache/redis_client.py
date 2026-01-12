import redis.asyncio as redis
from src.config import settings

class RedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Connect to Redis on app startup"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Close Redis connection on shutdown"""
        if self.redis:
            await self.redis.close()
    
    # Key-Value Operations
    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str):
        return await self.redis.set(key, value)
    
    async def setex(self, key: str, seconds: int, value: str):
        """Set key with expiration time"""
        return await self.redis.setex(key, seconds, value)
    
    async def delete(self, key: str):
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key) > 0
    
    # For rate limiting (bonus)
    async def incr(self, key: str) -> int:
        """Increment counter"""
        return await self.redis.incr(key)
    
    async def expire(self, key: str, seconds: int):
        """Set expiration on existing key"""
        return await self.redis.expire(key, seconds)

redis_client = RedisClient()
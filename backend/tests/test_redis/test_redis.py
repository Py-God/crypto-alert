# test_redis.py
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from src.cache.redis_client import redis_client

async def test_redis():
    print("Testing Redis connection...")
    
    # Connect
    await redis_client.connect()
    
    if not redis_client.is_connected():
        print("❌ Redis not connected")
        return
    
    print("✅ Redis connected")
    
    # Test set
    success = await redis_client.setex("test_key", 10, "test_value")
    print(f"Set test_key: {success}")
    
    # Test get
    value = await redis_client.get("test_key")
    print(f"Get test_key: {value}")
    
    # Test TTL
    ttl = await redis_client.ttl("test_key")
    print(f"TTL for test_key: {ttl} seconds")
    
    # Cleanup
    await redis_client.delete("test_key")
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_redis())
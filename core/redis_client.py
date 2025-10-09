"""Redis client for caching and token blacklist"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed. Token blacklist will use in-memory fallback.")


class RedisClient:
    """Redis client wrapper with fallback to in-memory storage"""
    
    def __init__(self):
        self.redis = None
        self.fallback_storage = {}  # In-memory fallback
    
    async def connect(self, redis_url: str):
        """
        Connect to Redis
        
        Args:
            redis_url: Redis connection URL
        """
        if not REDIS_AVAILABLE:
            logger.warning("Using in-memory storage instead of Redis")
            return
        
        try:
            self.redis = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}. Using in-memory fallback.")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis
        
        Args:
            key: Key to retrieve
            
        Returns:
            Value if found, None otherwise
        """
        if self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.error(f"Redis GET error: {str(e)}")
        
        # Fallback to in-memory
        return self.fallback_storage.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set value in Redis with optional expiry
        
        Args:
            key: Key to set
            value: Value to store
            ex: Expiry time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self.redis:
            try:
                await self.redis.set(key, value, ex=ex)
                return True
            except Exception as e:
                logger.error(f"Redis SET error: {str(e)}")
        
        # Fallback to in-memory
        self.fallback_storage[key] = value
        return True
    
    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """
        Set value with expiry time
        
        Args:
            key: Key to set
            seconds: Expiry time in seconds
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        return await self.set(key, value, ex=seconds)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key: Key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.redis:
            try:
                await self.redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis DELETE error: {str(e)}")
        
        # Fallback to in-memory
        if key in self.fallback_storage:
            del self.fallback_storage[key]
        return True
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        Args:
            key: Key to check
            
        Returns:
            True if exists, False otherwise
        """
        if self.redis:
            try:
                result = await self.redis.exists(key)
                return result > 0
            except Exception as e:
                logger.error(f"Redis EXISTS error: {str(e)}")
        
        # Fallback to in-memory
        return key in self.fallback_storage


# Global Redis client instance
redis_client = RedisClient()

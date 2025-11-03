"""Redis caching service for frequently accessed data."""
import json
import os
from typing import Any, Optional

import redis.asyncio as redis


class CacheService:
    """Async Redis cache service with graceful degradation."""

    def __init__(self):
        """Initialize Redis connection (optional - degrades gracefully if unavailable)."""
        redis_url = os.getenv("REDIS_URL")
        self.redis_client = None
        self.redis_available = False
        self.default_ttl = 300  # 5 minutes default TTL

        # Only connect if REDIS_URL is explicitly set
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                )
                self.redis_available = True
                print(f"✓ Redis cache connected: {redis_url}")
            except Exception as e:
                print(f"⚠ Redis cache unavailable (degrading gracefully): {e}")
                self.redis_client = None
                self.redis_available = False
        else:
            print("ℹ Redis cache disabled (REDIS_URL not set) - using memory cache fallback")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.redis_available or not self.redis_client:
            return None  # Cache miss when Redis unavailable

        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            # Log error but don't fail - cache misses are acceptable
            print(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: 300)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_available or not self.redis_client:
            return False  # Silently fail when Redis unavailable

        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.redis_available or not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "papers:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_available or not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_available or not self.redis_client:
            return False

        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment (default: 1)

        Returns:
            New value or None on error
        """
        if not self.redis_available or not self.redis_client:
            return None

        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error for key {key}: {e}")
            return None

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global cache instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get or create cache service instance.

    Returns:
        CacheService instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


async def close_cache():
    """Close cache connection."""
    global _cache_instance
    if _cache_instance is not None:
        await _cache_instance.close()
        _cache_instance = None

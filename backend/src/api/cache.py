"""
API response caching middleware for HypePaper.

Caches expensive hype score calculations for 1 hour to improve performance.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json


class SimpleCache:
    """
    Simple in-memory cache with TTL (Time To Live).

    For production, consider using Redis or Memcached.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, prefix: str, **params) -> str:
        """Generate cache key from prefix and parameters."""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if datetime.now() > entry["expires_at"]:
            # Expired - remove from cache
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(),
        }

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items() if now > entry["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now()
        valid_entries = sum(
            1 for entry in self._cache.values() if now <= entry["expires_at"]
        )
        expired_entries = len(self._cache) - valid_entries

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
        }


# Global cache instance
cache = SimpleCache()


def cache_hype_scores(topic_id: Optional[int] = None) -> str:
    """Generate cache key for hype score queries."""
    return cache._generate_key("hype_scores", topic_id=topic_id)


def cache_papers_list(
    topic_id: Optional[int] = None,
    sort_by: str = "hype",
    min_hype: float = 0.0,
    limit: int = 100,
) -> str:
    """Generate cache key for papers list queries."""
    return cache._generate_key(
        "papers_list",
        topic_id=topic_id,
        sort_by=sort_by,
        min_hype=min_hype,
        limit=limit,
    )


def cache_paper_metrics(paper_id: int) -> str:
    """Generate cache key for paper metrics queries."""
    return cache._generate_key("paper_metrics", paper_id=paper_id)

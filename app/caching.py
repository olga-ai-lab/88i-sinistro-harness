"""Caching module with Redis integration and graceful fallback.

Provides cache management with TTL, pattern-based invalidation, and decorator
for caching function results.
"""

from __future__ import annotations

import json
import logging
import functools
import time
from typing import Any, Callable, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available; using in-memory fallback cache")


class InMemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        """Initialize in-memory cache."""
        self.cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.
        """
        if key not in self.cache:
            return None

        value, expiry = self.cache[key]
        if expiry > 0 and time.time() > expiry:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (0 = no expiry).
        """
        expiry = time.time() + ttl if ttl > 0 else 0
        self.cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key.
        """
        self.cache.pop(key, None)

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Pattern with wildcards (e.g., 'user:*').

        Returns:
            Number of keys deleted.
        """
        import fnmatch
        keys_to_delete = [
            k for k in self.cache.keys()
            if fnmatch.fnmatch(k, pattern)
        ]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()


class RedisCache:
    """Redis-backed cache with graceful fallback."""

    def __init__(self, redis_url: str, fallback_to_memory: bool = True):
        """Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0').
            fallback_to_memory: If True, use in-memory cache if Redis unavailable.
        """
        self.redis_url = redis_url
        self.fallback_to_memory = fallback_to_memory
        self.client = None
        self.fallback_cache = InMemoryCache() if fallback_to_memory else None
        self._connected = False

        if not REDIS_AVAILABLE:
            logger.warning("Redis library not installed; using in-memory cache")
            return

        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis ({redis_url}): {e}. "
                f"Using {'in-memory' if fallback_to_memory else 'no'} fallback."
            )
            self.client = None
            if not fallback_to_memory:
                raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        # Try Redis first
        if self._connected and self.client:
            try:
                value = self.client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
                return None
            except Exception as e:
                logger.warning(f"Redis GET error: {e}")
                self._connected = False

        # Fall back to memory cache
        if self.fallback_cache:
            return self.fallback_cache.get(key)

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        # Try Redis first
        if self._connected and self.client:
            try:
                json_value = json.dumps(value) if not isinstance(value, str) else value
                if ttl > 0:
                    self.client.setex(key, ttl, json_value)
                else:
                    self.client.set(key, json_value)
                return
            except Exception as e:
                logger.warning(f"Redis SET error: {e}")
                self._connected = False

        # Fall back to memory cache
        if self.fallback_cache:
            self.fallback_cache.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key.
        """
        if self._connected and self.client:
            try:
                self.client.delete(key)
                return
            except Exception as e:
                logger.warning(f"Redis DELETE error: {e}")
                self._connected = False

        if self.fallback_cache:
            self.fallback_cache.delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Pattern with wildcards (e.g., 'user:*').

        Returns:
            Number of keys deleted.
        """
        if self._connected and self.client:
            try:
                keys = self.client.keys(pattern)
                if keys:
                    return self.client.delete(*keys)
                return 0
            except Exception as e:
                logger.warning(f"Redis DELETE_PATTERN error: {e}")
                self._connected = False

        if self.fallback_cache:
            return self.fallback_cache.delete_pattern(pattern)

        return 0

    def clear(self) -> None:
        """Clear all cached data."""
        if self._connected and self.client:
            try:
                self.client.flushdb()
                return
            except Exception as e:
                logger.warning(f"Redis CLEAR error: {e}")
                self._connected = False

        if self.fallback_cache:
            self.fallback_cache.clear()


class CacheManager:
    """Unified cache manager supporting both Redis and in-memory backends."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize CacheManager.

        Args:
            redis_url: Redis connection URL. If None, uses in-memory cache.
        """
        if redis_url:
            self.cache = RedisCache(redis_url, fallback_to_memory=True)
        else:
            self.cache = InMemoryCache()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (0 = no expiry).
        """
        self.cache.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key.
        """
        self.cache.delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Pattern with wildcards.

        Returns:
            Number of keys deleted.
        """
        return self.cache.delete_pattern(pattern)

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()

    def cache_decorator(
        self, ttl: int = 3600, key_prefix: str = ""
    ) -> Callable:
        """Decorator for caching function results.

        Args:
            ttl: Time to live in seconds.
            key_prefix: Prefix for cache keys (e.g., 'user:').

        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Build cache key from function name and arguments
                cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"

                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"Cache miss (populated): {cache_key}")
                return result

            return wrapper

        return decorator

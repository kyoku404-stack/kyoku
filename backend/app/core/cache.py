"""KEEP Enterprise Platform — Redis Cache & Rate Limiting Subsystem.

Provides asynchronous Redis caching, counter tracking, and rate limiting with
seamless in-memory fallback for local development and test environments.
Derived from devdocs/p1/p1.7.txt and docs/Architecture/dashboard-architecture.md Section 9.3 & 12.
"""

import asyncio
import logging
import time
from typing import Any, cast

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class CacheManager:
    """Manages Redis cache operations with resilient in-memory fallback."""

    def __init__(self) -> None:
        self._redis_client: Any = None
        self._in_memory_cache: dict[str, tuple[str, float]] = {}
        self._in_memory_counters: dict[str, tuple[int, float]] = {}
        self._in_memory_rate_limits: dict[str, list[float]] = {}
        self._redis_connected: bool | None = None

    async def get_client(self) -> Any:
        """Lazily initializes and returns the async Redis client."""
        if not HAS_REDIS or self._redis_connected is False:
            return None

        if self._redis_client is None:
            try:
                redis_url = settings.REDIS_URL or "redis://127.0.0.1:6379/0"
                if "localhost" in redis_url:
                    redis_url = redis_url.replace("localhost", "127.0.0.1")
                client = aioredis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.05,
                    socket_timeout=0.05,
                )
                await asyncio.wait_for(client.ping(), timeout=0.05)
                self._redis_client = client
                self._redis_connected = True
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Could not connect to Redis: {e}. Using in-memory fallback.")
                self._redis_connected = False
                self._redis_client = None
                return None
        return cast(Any, self._redis_client)

    async def get(self, key: str) -> str | None:
        """Retrieves string value from cache."""
        client = await self.get_client()
        if client:
            try:
                val = await client.get(key)
                return str(val) if val is not None else None
            except Exception as e:  # noqa: BLE001
                self._redis_connected = False
                self._redis_client = None
                logger.debug(f"Redis get failed for {key}: {e}. Falling back to in-memory.")


        # In-memory fallback
        now = time.time()
        if key in self._in_memory_cache:
            val_mem, expiry = self._in_memory_cache[key]
            if expiry > now:
                return val_mem
            del self._in_memory_cache[key]
        return None

    async def set(self, key: str, value: str, ttl: int = 60) -> bool:
        """Sets string value in cache with expiration in seconds."""
        client = await self.get_client()
        if client:
            try:
                await client.set(key, value, ex=ttl)
                return True
            except Exception as e:  # noqa: BLE001
                self._redis_connected = False
                self._redis_client = None
                logger.debug(f"Redis set failed for {key}: {e}. Falling back to in-memory.")


        # In-memory fallback
        self._in_memory_cache[key] = (value, time.time() + ttl)
        return True

    async def delete(self, key: str) -> bool:
        """Deletes a key from cache."""
        client = await self.get_client()
        if client:
            try:
                await client.delete(key)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis delete failed for {key}: {e}.")

        if key in self._in_memory_cache:
            del self._in_memory_cache[key]
        return True

    async def delete_pattern(self, pattern: str) -> int:
        """Deletes keys matching a wildcard pattern."""
        deleted = 0
        client = await self.get_client()
        if client:
            try:
                keys = await client.keys(pattern)
                if keys:
                    del_result = await client.delete(*keys)
                    return int(del_result) if del_result is not None else 0
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis delete_pattern failed for {pattern}: {e}.")

        # In-memory fallback
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in self._in_memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del self._in_memory_cache[k]
            deleted += 1
        return deleted

    async def incr(self, key: str, ttl: int = 86400) -> int:
        """Increments integer counter with expiration."""
        client = await self.get_client()
        if client:
            try:
                val = await client.incr(key)
                if val == 1:
                    await client.expire(key, ttl)
                return int(val)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis incr failed for {key}: {e}.")

        # In-memory fallback
        now = time.time()
        if key in self._in_memory_counters:
            count, expiry = self._in_memory_counters[key]
            if expiry > now:
                new_count = count + 1
                self._in_memory_counters[key] = (new_count, expiry)
                return new_count

        self._in_memory_counters[key] = (1, now + ttl)
        return 1

    async def get_counter(self, key: str) -> int:
        """Reads integer counter value."""
        client = await self.get_client()
        if client:
            try:
                val = await client.get(key)
                return int(val) if val else 0
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis get_counter failed for {key}: {e}.")

        now = time.time()
        if key in self._in_memory_counters:
            count, expiry = self._in_memory_counters[key]
            if expiry > now:
                return count
            del self._in_memory_counters[key]
        return 0

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int = 60,
        window_seconds: int = 3600,
    ) -> tuple[bool, int]:
        """Sliding-window rate limiter.

        Args:
            identifier: Rate limit bucket key (e.g., user_id).
            limit: Maximum allowed requests in window.
            window_seconds: Window duration in seconds.

        Returns:
            Tuple of (is_allowed: bool, remaining_requests: int).
        """
        key = f"ratelimit:{identifier}"
        now = time.time()
        client = await self.get_client()

        if client:
            try:
                pipe = client.pipeline()
                pipe.zremrangebyscore(key, 0, now - window_seconds)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window_seconds)
                results = await pipe.execute()
                count = int(results[1]) if len(results) > 1 else 0
                is_allowed = bool(count < limit)
                remaining = max(0, limit - count)
                return is_allowed, remaining
            except Exception as e:  # noqa: BLE001
                self._redis_connected = False
                self._redis_client = None
                logger.debug(f"Redis rate limit failed for {key}: {e}. Falling back to in-memory.")


        # In-memory fallback
        timestamps = self._in_memory_rate_limits.setdefault(key, [])
        valid_timestamps = [ts for ts in timestamps if ts > (now - window_seconds)]
        if len(valid_timestamps) >= limit:
            self._in_memory_rate_limits[key] = valid_timestamps
            return False, 0

        valid_timestamps.append(now)
        self._in_memory_rate_limits[key] = valid_timestamps
        remaining = limit - len(valid_timestamps)
        return True, max(0, remaining)

    def clear_in_memory(self) -> None:
        """Clears all in-memory cache data (useful for test resets)."""
        self._in_memory_cache.clear()
        self._in_memory_counters.clear()
        self._in_memory_rate_limits.clear()


cache = CacheManager()

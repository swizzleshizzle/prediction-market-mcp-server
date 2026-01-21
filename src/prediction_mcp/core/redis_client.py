"""
Redis Client for Prediction Market MCP Server.

Provides:
- JSON document storage (RedisJSON)
- Caching with TTL
- State persistence for strategies and positions
- Market data caching
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client wrapper.

    Supports RedisJSON for document storage and standard
    Redis operations for caching.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        db: int = 0,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL
            db: Database number
            decode_responses: Whether to decode responses to strings
        """
        self.url = url
        self.db = db
        self.decode_responses = decode_responses
        self._redis: Optional[redis.Redis] = None

    async def connect(self) -> bool:
        """
        Connect to Redis.

        Returns:
            True if connection successful
        """
        try:
            self._redis = redis.from_url(
                self.url,
                db=self.db,
                decode_responses=self.decode_responses,
            )
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._redis is not None

    # === JSON Operations (RedisJSON) ===

    async def json_set(
        self,
        key: str,
        value: Any,
        path: str = "$",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store JSON document.

        Args:
            key: Redis key
            value: JSON-serializable value
            path: JSONPath (default: root)
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            await self._redis.json().set(key, path, value)
            if ttl:
                await self._redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"JSON set failed for {key}: {e}")
            return False

    async def json_get(
        self,
        key: str,
        path: str = "$",
    ) -> Optional[Any]:
        """
        Retrieve JSON document.

        Args:
            key: Redis key
            path: JSONPath (default: root)

        Returns:
            JSON value or None
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            result = await self._redis.json().get(key, path)
            # RedisJSON returns list for $ path
            if isinstance(result, list) and len(result) == 1:
                return result[0]
            return result
        except Exception as e:
            logger.debug(f"JSON get failed for {key}: {e}")
            return None

    async def json_delete(self, key: str) -> bool:
        """
        Delete JSON document.

        Args:
            key: Redis key

        Returns:
            True if deleted
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"JSON delete failed for {key}: {e}")
            return False

    # === Cache Operations ===

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """
        Cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 5 minutes)

        Returns:
            True if successful
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False

    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Cache get failed for {key}: {e}")
            return None

    async def cache_delete(self, key: str) -> bool:
        """
        Delete cached value.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {e}")
            return False

    async def cache_exists(self, key: str) -> bool:
        """
        Check if cache key exists.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists check failed for {key}: {e}")
            return False

    # === Hash Operations ===

    async def hash_set(
        self,
        key: str,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set hash fields.

        Args:
            key: Hash key
            mapping: Field-value mapping
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            # Serialize values
            serialized = {k: json.dumps(v) for k, v in mapping.items()}
            await self._redis.hset(key, mapping=serialized)
            if ttl:
                await self._redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Hash set failed for {key}: {e}")
            return False

    async def hash_get(
        self,
        key: str,
        field: Optional[str] = None,
    ) -> Optional[Union[Any, Dict[str, Any]]]:
        """
        Get hash field(s).

        Args:
            key: Hash key
            field: Specific field (None for all)

        Returns:
            Field value or all fields
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            if field:
                value = await self._redis.hget(key, field)
                return json.loads(value) if value else None
            else:
                values = await self._redis.hgetall(key)
                return {k: json.loads(v) for k, v in values.items()} if values else None
        except Exception as e:
            logger.debug(f"Hash get failed for {key}: {e}")
            return None

    # === List Operations ===

    async def list_push(
        self,
        key: str,
        *values: Any,
        max_length: Optional[int] = None,
    ) -> int:
        """
        Push values to list.

        Args:
            key: List key
            values: Values to push
            max_length: Trim list to this length

        Returns:
            List length after push
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            serialized = [json.dumps(v) for v in values]
            length = await self._redis.rpush(key, *serialized)

            if max_length:
                await self._redis.ltrim(key, -max_length, -1)

            return length
        except Exception as e:
            logger.error(f"List push failed for {key}: {e}")
            return 0

    async def list_get(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
    ) -> List[Any]:
        """
        Get list values.

        Args:
            key: List key
            start: Start index
            end: End index (-1 for all)

        Returns:
            List of values
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            values = await self._redis.lrange(key, start, end)
            return [json.loads(v) for v in values]
        except Exception as e:
            logger.debug(f"List get failed for {key}: {e}")
            return []

    # === Key Management ===

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: Key pattern

        Returns:
            List of matching keys
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            return await self._redis.keys(pattern)
        except Exception as e:
            logger.error(f"Keys failed for pattern {pattern}: {e}")
            return []

    async def delete(self, *keys: str) -> int:
        """
        Delete keys.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            return await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set key expiration.

        Args:
            key: Key to expire
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        try:
            return await self._redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Expire failed for {key}: {e}")
            return False


def create_redis_client(
    url: str = "redis://localhost:6379",
    db: int = 0,
) -> RedisClient:
    """
    Factory function to create RedisClient.

    Args:
        url: Redis connection URL
        db: Database number

    Returns:
        Configured RedisClient
    """
    return RedisClient(url=url, db=db)

"""Tests for Redis integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisClient:
    """Test Redis client wrapper."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Should connect to Redis."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            connected = await client.connect()

            assert connected is True
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_json_operations(self):
        """Should store and retrieve JSON documents."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()

            # Mock json() to return an object with async methods
            mock_json = MagicMock()
            mock_json.set = AsyncMock(return_value=True)
            mock_json.get = AsyncMock(return_value=[{"name": "test"}])  # RedisJSON returns list
            mock_redis.json = MagicMock(return_value=mock_json)
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            client._redis = mock_redis

            # Set JSON
            await client.json_set("test:key", {"name": "test"})
            mock_json.set.assert_called()

            # Get JSON
            result = await client.json_get("test:key")
            assert result == {"name": "test"}

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Should cache and retrieve values with TTL."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.setex = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value=b'{"cached": true}')
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            client._redis = mock_redis

            # Cache value
            await client.cache_set("cache:key", {"cached": True}, ttl=300)
            mock_redis.setex.assert_called()

            # Get cached value
            result = await client.cache_get("cache:key")
            assert result == {"cached": True}

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Should disconnect cleanly."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            client._redis = mock_redis

            await client.disconnect()

            mock_redis.close.assert_called_once()


class TestRedisClientConfig:
    """Test Redis client configuration."""

    def test_default_url(self):
        """Should use default Redis URL."""
        from src.prediction_mcp.core.redis_client import RedisClient

        client = RedisClient()
        assert client.url == "redis://localhost:6379"

    def test_custom_url(self):
        """Should accept custom Redis URL."""
        from src.prediction_mcp.core.redis_client import RedisClient

        client = RedisClient("redis://custom:6380/1")
        assert client.url == "redis://custom:6380/1"

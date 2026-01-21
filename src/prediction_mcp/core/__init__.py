"""
Core utilities for the Prediction Market MCP Server.

Provides:
- Redis client for caching and state persistence
- Common utilities shared across platforms
"""

from .redis_client import RedisClient, create_redis_client

__all__ = ["RedisClient", "create_redis_client"]

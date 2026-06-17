"""
Redis client for caching and session management.
"""
import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


class RedisCache:
    """Helper class for Redis cache operations."""

    def __init__(self, prefix: str = "idobetz"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        client = await get_redis()
        value = await client.get(self._key(key))
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        client = await get_redis()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return await client.setex(self._key(key), ttl, serialized)

    async def delete(self, key: str) -> bool:
        client = await get_redis()
        return bool(await client.delete(self._key(key)))

    async def exists(self, key: str) -> bool:
        client = await get_redis()
        return bool(await client.exists(self._key(key)))

    async def incr(self, key: str, ttl: Optional[int] = None) -> int:
        client = await get_redis()
        value = await client.incr(self._key(key))
        if ttl and value == 1:
            await client.expire(self._key(key), ttl)
        return value

    async def hset(self, key: str, field: str, value: Any) -> bool:
        client = await get_redis()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return bool(await client.hset(self._key(key), field, serialized))

    async def hget(self, key: str, field: str) -> Optional[Any]:
        client = await get_redis()
        value = await client.hget(self._key(key), field)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def hgetall(self, key: str) -> dict:
        client = await get_redis()
        data = await client.hgetall(self._key(key))
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v
        return result

    async def publish(self, channel: str, message: Any) -> int:
        client = await get_redis()
        serialized = json.dumps(message) if not isinstance(message, str) else message
        return await client.publish(channel, serialized)


# Singleton cache instances
session_cache = RedisCache(prefix="session")
product_cache = RedisCache(prefix="product")
user_cache = RedisCache(prefix="user")
rate_limit_cache = RedisCache(prefix="ratelimit")

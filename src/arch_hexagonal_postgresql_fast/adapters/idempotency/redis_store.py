"""Redis idempotency store adapter."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis


class RedisIdempotencyStore:
    """Redis implementation of idempotency store."""

    def __init__(self, redis_url: str) -> None:
        """Initialize store with Redis URL."""
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = redis.from_url(self._redis_url)  # type: ignore[no-untyped-call]

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()

    async def is_duplicate(self, key: str) -> bool:
        """Check if key has been used before."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        exists = await self._redis.exists(self._get_key(key))
        return bool(exists)

    async def get_result(self, key: str) -> dict[str, Any] | None:
        """Get cached result for idempotency key."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        data = await self._redis.get(self._get_key(key))
        if data:
            result: dict[str, Any] = json.loads(data)
            return result
        return None

    async def store_result(self, key: str, result: dict[str, Any], ttl: int = 86400) -> None:
        """Store result for idempotency key."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        await self._redis.setex(
            self._get_key(key),
            ttl,
            json.dumps(result),
        )

    async def delete(self, key: str) -> None:
        """Delete idempotency key."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        await self._redis.delete(self._get_key(key))

    def _get_key(self, key: str) -> str:
        """Get prefixed Redis key."""
        return f"idempotency:{key}"

"""Idempotency store port."""

from __future__ import annotations

from typing import Any, Protocol


class IdempotencyStore(Protocol):
    """Interface for idempotency key storage."""

    async def is_duplicate(self, key: str) -> bool:
        """Check if key has been used before."""
        ...

    async def get_result(self, key: str) -> dict[str, Any] | None:
        """Get cached result for idempotency key."""
        ...

    async def store_result(self, key: str, result: dict[str, Any], ttl: int = 86400) -> None:
        """Store result for idempotency key.

        Args:
            key: Idempotency key
            result: Result to cache
            ttl: Time to live in seconds (default 24 hours)
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete idempotency key."""
        ...

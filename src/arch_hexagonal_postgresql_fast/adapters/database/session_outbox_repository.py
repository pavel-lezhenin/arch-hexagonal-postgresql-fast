"""Session-managed OutboxRepository for background workers."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from arch_hexagonal_postgresql_fast.adapters.database.postgresql_outbox_repository import (
    PostgreSQLOutboxRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxEvent,
    OutboxRepository,
)


class SessionManagedOutboxRepository(OutboxRepository):
    """OutboxRepository that creates new sessions for each operation.

    Useful for background workers that need independent sessions.
    """

    def __init__(
        self,
        session_factory: Callable[[], Coroutine[Any, Any, AsyncSession]],
    ) -> None:
        """Initialize with async session factory."""
        self._session_factory = session_factory

    async def save(self, event: OutboxEvent) -> None:
        """Save outbox event using new session."""
        async with await self._get_session() as session:
            repo = PostgreSQLOutboxRepository(session)
            await repo.save(event)
            await session.commit()

    async def get_unpublished(self, limit: int = 100) -> list[OutboxEvent]:
        """Get unpublished events using new session."""
        async with await self._get_session() as session:
            repo = PostgreSQLOutboxRepository(session)
            return await repo.get_unpublished(limit)

    async def mark_published(self, event_id: UUID) -> None:
        """Mark event as published using new session."""
        async with await self._get_session() as session:
            repo = PostgreSQLOutboxRepository(session)
            await repo.mark_published(event_id)
            await session.commit()

    async def increment_attempts(self, event_id: UUID, error: str) -> None:
        """Increment attempts using new session."""
        async with await self._get_session() as session:
            repo = PostgreSQLOutboxRepository(session)
            await repo.increment_attempts(event_id, error)
            await session.commit()

    async def get_failed(self, max_attempts: int = 5) -> list[OutboxEvent]:
        """Get failed events using new session."""
        async with await self._get_session() as session:
            repo = PostgreSQLOutboxRepository(session)
            return await repo.get_failed(max_attempts)

    async def _get_session(self) -> AsyncSession:
        """Get new session from factory."""
        return await self._session_factory()

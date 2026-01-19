"""PostgreSQL implementation of OutboxRepository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxEvent,
    OutboxRepository,
)

from .outbox_event_model import OutboxEventModel


class PostgreSQLOutboxRepository(OutboxRepository):
    """PostgreSQL implementation of OutboxRepository using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self._session = session

    async def save(self, event: OutboxEvent) -> None:
        """Save outbox event to database."""
        model = OutboxEventModel(
            id=event.id,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            event_type=event.event_type,
            payload=event.payload,
            created_at=event.created_at,
            published_at=event.published_at,
            attempts=event.attempts,
            last_error=event.last_error,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_unpublished(self, limit: int = 100) -> list[OutboxEvent]:
        """Get unpublished events ordered by creation time."""
        stmt = (
            select(OutboxEventModel)
            .where(OutboxEventModel.published_at.is_(None))
            .order_by(OutboxEventModel.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def mark_published(self, event_id: UUID) -> None:
        """Mark event as successfully published."""
        stmt = select(OutboxEventModel).where(OutboxEventModel.id == event_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.published_at = datetime.now(UTC)
        await self._session.flush()

    async def increment_attempts(self, event_id: UUID, error: str) -> None:
        """Increment retry attempts and record error."""
        stmt = select(OutboxEventModel).where(OutboxEventModel.id == event_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.attempts += 1
        model.last_error = error
        await self._session.flush()

    async def get_failed(self, max_attempts: int = 5) -> list[OutboxEvent]:
        """Get events that exceeded max retry attempts."""
        stmt = (
            select(OutboxEventModel)
            .where(
                OutboxEventModel.attempts >= max_attempts,
                OutboxEventModel.published_at.is_(None),
            )
            .order_by(OutboxEventModel.created_at)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: OutboxEventModel) -> OutboxEvent:
        """Convert SQLAlchemy model to domain OutboxEvent."""
        return OutboxEvent(
            id=model.id,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            event_type=model.event_type,
            payload=model.payload,
            created_at=model.created_at,
            published_at=model.published_at,
            attempts=model.attempts,
            last_error=model.last_error,
        )

"""Outbox repository port for managing outbox events."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID


class OutboxEvent:
    """Outbox event data structure."""

    def __init__(
        self,
        id: UUID,  # noqa: A002
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, object],
        created_at: datetime,
        published_at: datetime | None = None,
        attempts: int = 0,
        last_error: str | None = None,
    ) -> None:
        """Initialize outbox event."""
        self.id = id
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.payload = payload
        self.created_at = created_at
        self.published_at = published_at
        self.attempts = attempts
        self.last_error = last_error


class OutboxRepository(Protocol):
    """Port for outbox event persistence."""

    async def save(self, event: OutboxEvent) -> None:
        """Save outbox event to storage.

        Args:
            event: Outbox event to save

        """
        ...

    async def get_unpublished(self, limit: int = 100) -> list[OutboxEvent]:
        """Get unpublished events ordered by creation time.

        Args:
            limit: Maximum number of events to retrieve

        Returns:
            List of unpublished outbox events

        """
        ...

    async def mark_published(self, event_id: UUID) -> None:
        """Mark event as successfully published.

        Args:
            event_id: ID of the event to mark as published

        """
        ...

    async def increment_attempts(self, event_id: UUID, error: str) -> None:
        """Increment retry attempts and record error.

        Args:
            event_id: ID of the event
            error: Error message from failed attempt

        """
        ...

    async def get_failed(self, max_attempts: int = 5) -> list[OutboxEvent]:
        """Get events that exceeded max retry attempts.

        Args:
            max_attempts: Maximum number of allowed attempts

        Returns:
            List of failed events for DLQ processing

        """
        ...

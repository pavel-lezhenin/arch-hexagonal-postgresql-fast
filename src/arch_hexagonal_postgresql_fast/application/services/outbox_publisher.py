"""Outbox publisher service for reliable event publishing."""

from __future__ import annotations

import logging
from uuid import UUID

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from arch_hexagonal_postgresql_fast.application.ports.event_publisher import (
    EventPublisher,
)
from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxRepository,
)

logger = logging.getLogger(__name__)


class OutboxPublisherService:
    """Service for publishing outbox events to message queue."""

    def __init__(
        self,
        outbox_repo: OutboxRepository,
        event_publisher: EventPublisher,
        max_attempts: int = 5,
    ) -> None:
        """Initialize outbox publisher service."""
        self._outbox_repo = outbox_repo
        self._event_publisher = event_publisher
        self._max_attempts = max_attempts

    async def publish_pending_events(self, batch_size: int = 100) -> int:
        """Publish pending events from outbox.

        Args:
            batch_size: Number of events to process in one batch

        Returns:
            Number of successfully published events

        """
        events = await self._outbox_repo.get_unpublished(limit=batch_size)
        published_count = 0

        for event in events:
            try:
                await self._publish_event_with_retry(event.id)
                published_count += 1
            except Exception:  # noqa: S110 # nosec B110
                # Logged in _publish_event_with_retry
                # Event will be moved to DLQ by separate process
                pass

        return published_count

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _publish_event_with_retry(self, event_id: UUID) -> None:
        """Publish single event with retry logic."""
        # Get fresh event data
        events = await self._outbox_repo.get_unpublished(limit=1000)
        event = next((e for e in events if e.id == event_id), None)

        if event is None or event.published_at is not None:
            # Already published or deleted
            return

        try:
            # Publish to message queue via generic publish_event method
            routing_key = f"{event.aggregate_type.lower()}s"  # e.g., "payments"
            await self._event_publisher.publish_event(
                event_type=event.event_type,
                payload=event.payload,
                routing_key=routing_key,
            )

            # Mark as published only after successful send
            await self._outbox_repo.mark_published(event_id)

            logger.info(
                "Published event %s: %s for %s/%s",
                event.id,
                event.event_type,
                event.aggregate_type,
                event.aggregate_id,
            )

        except Exception as e:
            # Record failure
            await self._outbox_repo.increment_attempts(event_id, str(e))
            logger.warning("Failed to publish event %s: %s", event_id, e)
            raise

    async def get_failed_events_count(self) -> int:
        """Get count of events that exceeded max attempts."""
        failed = await self._outbox_repo.get_failed(max_attempts=self._max_attempts)
        return len(failed)

"""Background worker for publishing outbox events."""

from __future__ import annotations

import asyncio
import logging

from arch_hexagonal_postgresql_fast.application.services.outbox_publisher import (
    OutboxPublisherService,
)

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Background worker for processing outbox events."""

    def __init__(
        self,
        publisher_service: OutboxPublisherService,
        interval_seconds: int = 5,
    ) -> None:
        """Initialize outbox worker."""
        self._publisher = publisher_service
        self._interval = interval_seconds
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            logger.warning("Outbox worker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Outbox worker started (interval: %ds)", self._interval)

    async def stop(self) -> None:
        """Stop the background worker."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox worker stopped")

    async def _run(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                published_count = await self._publisher.publish_pending_events()
                if published_count > 0:
                    logger.info("Published %d outbox events", published_count)

                failed_count = await self._publisher.get_failed_events_count()
                if failed_count > 0:
                    logger.warning("%d events in DLQ (failed)", failed_count)

            except Exception as e:
                logger.error("Error in outbox worker: %s", e, exc_info=True)

            # Wait before next iteration
            await asyncio.sleep(self._interval)

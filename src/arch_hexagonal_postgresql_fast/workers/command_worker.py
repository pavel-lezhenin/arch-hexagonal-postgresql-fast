"""Command worker for consuming and processing commands."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from arch_hexagonal_postgresql_fast.adapters.messaging.rabbitmq_command_consumer import (
    RabbitMQCommandConsumer,
)

if TYPE_CHECKING:
    from arch_hexagonal_postgresql_fast.application.handlers.command_handler import (
        CommandHandler,
    )

logger = logging.getLogger(__name__)


class CommandWorker:
    """Worker for consuming commands from RabbitMQ."""

    def __init__(
        self,
        consumer: RabbitMQCommandConsumer,
        handler: CommandHandler,
        queue_name: str = "payment.commands.process",
    ) -> None:
        """Initialize command worker."""
        self._consumer = consumer
        self._handler = handler
        self._queue_name = queue_name
        self._running = False

    async def start(self) -> None:
        """Start the command worker."""
        if self._running:
            logger.warning("Command worker already running")
            return

        self._running = True

        try:
            # Connect to RabbitMQ
            await self._consumer.connect()

            # Start consuming
            await self._consumer.start_consuming(
                queue_name=self._queue_name,
                callback=self._handler.handle_message,
            )

            logger.info(
                "Command worker started (queue: %s)",
                self._queue_name,
            )

            # Keep running
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error("Error in command worker: %s", e, exc_info=True)
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the command worker."""
        if not self._running:
            return

        self._running = False
        await self._consumer.stop_consuming()
        await self._consumer.disconnect()
        logger.info("Command worker stopped")

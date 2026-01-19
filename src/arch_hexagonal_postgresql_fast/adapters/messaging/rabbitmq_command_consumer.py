"""RabbitMQ implementation of CommandConsumer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class RabbitMQCommandConsumer:
    """RabbitMQ implementation of command consumer."""

    def __init__(self, rabbitmq_url: str) -> None:
        """Initialize consumer with RabbitMQ connection URL."""
        self._url = rabbitmq_url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        self._connection = await connect_robust(self._url)
        self._channel = await self._connection.channel()
        # Set prefetch count for fair distribution
        if self._channel:
            await self._channel.set_qos(prefetch_count=1)
        logger.info("RabbitMQ command consumer connected")

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()
        logger.info("RabbitMQ command consumer disconnected")

    async def start_consuming(
        self,
        queue_name: str,
        callback: Callable[[AbstractIncomingMessage], Awaitable[None]],
    ) -> None:
        """Start consuming commands from queue.

        Args:
            queue_name: Name of the queue to consume from
            callback: Async function to handle incoming messages

        """
        if not self._channel:
            msg = "Not connected to RabbitMQ"
            raise RuntimeError(msg)

        # Declare queue (idempotent)
        self._queue = await self._channel.declare_queue(
            queue_name,
            durable=True,  # Survive broker restart
        )

        logger.info("Starting to consume from queue: %s", queue_name)

        # Start consuming
        await self._queue.consume(callback)

    async def stop_consuming(self) -> None:
        """Stop consuming commands."""
        # Consumer will stop when connection is closed
        logger.info("Stopped consuming from queue")

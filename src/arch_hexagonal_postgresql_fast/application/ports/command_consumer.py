"""Command consumer port for receiving commands from RabbitMQ."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aio_pika.abc import AbstractIncomingMessage


class CommandConsumer(Protocol):
    """Port for consuming commands from message queue."""

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
        ...

    async def stop_consuming(self) -> None:
        """Stop consuming commands and cleanup resources."""
        ...

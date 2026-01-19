"""Event consumer for logging payment events."""

from __future__ import annotations

import asyncio
import json
import logging

from aio_pika import connect_robust
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage

logger = logging.getLogger(__name__)


class LoggerEventConsumer:
    """Consumer that logs all payment events for observability."""

    def __init__(self, rabbitmq_url: str) -> None:
        """Initialize logger consumer."""
        self._url = rabbitmq_url
        self._connection: AbstractConnection | None = None
        self._running = False

    async def start(self) -> None:
        """Start consuming payment events."""
        if self._running:
            logger.warning("Logger consumer already running")
            return

        self._running = True
        self._connection = await connect_robust(self._url)
        channel = await self._connection.channel()

        # Set QoS
        await channel.set_qos(prefetch_count=10)

        # Declare exchange for payment events
        exchange = await channel.declare_exchange(
            "payment.events",
            durable=True,
        )

        # Declare queue for logging
        queue = await channel.declare_queue(
            "payment.events.logger",
            durable=True,
        )

        # Bind to all payment events
        await queue.bind(exchange, routing_key="Payment.*")

        logger.info("Logger event consumer started, listening to payment events")

        # Consume messages
        await queue.consume(self._handle_message)

        # Keep running
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop consuming events."""
        self._running = False
        if self._connection:
            await self._connection.close()
        logger.info("Logger event consumer stopped")

    async def _handle_message(self, message: AbstractIncomingMessage) -> None:
        """Handle incoming event message."""
        async with message.process():
            try:
                event = json.loads(message.body.decode())

                # Extract event details
                event_type = event.get("event_type", "unknown")
                aggregate_id = event.get("aggregate_id", "unknown")
                payload = event.get("payload", {})

                # Log event with structured data
                logger.info(
                    "PAYMENT EVENT: %s (aggregate: %s)",
                    event_type,
                    aggregate_id,
                    extra={
                        "event_type": event_type,
                        "aggregate_type": event.get("aggregate_type"),
                        "aggregate_id": aggregate_id,
                        "payload": payload,
                    },
                )

            except Exception as e:
                logger.error("Error processing event: %s", e, exc_info=True)
                # Don't requeue, just log and continue


async def main() -> None:
    """Run logger consumer."""
    from arch_hexagonal_postgresql_fast.config import Settings

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    settings = Settings()
    consumer = LoggerEventConsumer(settings.rabbitmq_url)

    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())

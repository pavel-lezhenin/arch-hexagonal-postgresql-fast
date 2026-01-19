"""Entry point for outbox worker."""

from __future__ import annotations

import asyncio
import logging
import sys

from arch_hexagonal_postgresql_fast.adapters.database.postgresql_outbox_repository import (
    PostgreSQLOutboxRepository,
)
from arch_hexagonal_postgresql_fast.adapters.messaging.rabbitmq_publisher import (
    RabbitMQEventPublisher,
)
from arch_hexagonal_postgresql_fast.application.services.outbox_publisher import (
    OutboxPublisherService,
)
from arch_hexagonal_postgresql_fast.config import Settings
from arch_hexagonal_postgresql_fast.workers.outbox_worker import OutboxWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run outbox worker."""
    settings = Settings()

    logger.info("Starting Outbox Worker...")
    logger.info("Database: %s", settings.database_url.split("@")[-1])
    logger.info("RabbitMQ: %s", settings.rabbitmq_url.split("@")[-1])

    # Create database session
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Create dependencies
    async with session_maker() as session:
        outbox_repo = PostgreSQLOutboxRepository(session)
        event_publisher = RabbitMQEventPublisher(settings.rabbitmq_url)

        # Connect to RabbitMQ
        await event_publisher.connect()

        try:
            # Create publisher service
            publisher_service = OutboxPublisherService(
                outbox_repo=outbox_repo,
                event_publisher=event_publisher,
                max_attempts=5,
            )

            # Create and start worker
            worker = OutboxWorker(
                publisher_service=publisher_service,
                interval_seconds=5,
            )

            await worker.start()

            # Keep running
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await worker.stop()
            await event_publisher.disconnect()
            await engine.dispose()

    logger.info("Outbox Worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        sys.exit(0)

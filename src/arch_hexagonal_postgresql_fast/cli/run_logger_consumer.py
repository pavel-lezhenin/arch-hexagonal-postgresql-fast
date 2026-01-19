"""Entry point for logger event consumer."""

from __future__ import annotations

import asyncio
import logging
import sys

from arch_hexagonal_postgresql_fast.config import Settings
from arch_hexagonal_postgresql_fast.workers.logger_event_consumer import (
    LoggerEventConsumer,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run logger event consumer."""
    settings = Settings()

    logger.info("Starting Logger Event Consumer...")
    logger.info("RabbitMQ: %s", settings.rabbitmq_url.split("@")[-1])

    consumer = LoggerEventConsumer(settings.rabbitmq_url)

    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await consumer.stop()

    logger.info("Logger Event Consumer stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        sys.exit(0)

"""Entry point for command worker."""

from __future__ import annotations

import asyncio
import logging
import sys

from arch_hexagonal_postgresql_fast.adapters.database.postgresql_outbox_repository import (
    PostgreSQLOutboxRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.postgresql_payment_repository import (
    PostgreSQLPaymentRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.postgresql_transaction_repository import (
    PostgreSQLTransactionRepository,
)
from arch_hexagonal_postgresql_fast.adapters.idempotency.redis_store import (
    RedisIdempotencyStore,
)
from arch_hexagonal_postgresql_fast.adapters.messaging.rabbitmq_command_consumer import (
    RabbitMQCommandConsumer,
)
from arch_hexagonal_postgresql_fast.adapters.messaging.rabbitmq_publisher import (
    RabbitMQEventPublisher,
)
from arch_hexagonal_postgresql_fast.adapters.payment_providers.stripe_adapter import (
    StripeAdapter,
)
from arch_hexagonal_postgresql_fast.application.handlers.command_handler import (
    CommandHandler,
)
from arch_hexagonal_postgresql_fast.application.use_cases.process_payment import (
    ProcessPayment,
)
from arch_hexagonal_postgresql_fast.config import Settings
from arch_hexagonal_postgresql_fast.workers.command_worker import CommandWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run command worker."""
    settings = Settings()

    logger.info("Starting Command Worker...")
    logger.info("Database: %s", settings.database_url.split("@")[-1])
    logger.info("RabbitMQ: %s", settings.rabbitmq_url.split("@")[-1])

    # Create database session
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Create dependencies
    async with session_maker() as session:
        # Repositories
        payment_repo = PostgreSQLPaymentRepository(session)
        transaction_repo = PostgreSQLTransactionRepository(session)
        outbox_repo = PostgreSQLOutboxRepository(session)

        # External services
        event_publisher = RabbitMQEventPublisher(settings.rabbitmq_url)
        await event_publisher.connect()

        payment_provider = StripeAdapter(settings.stripe_api_key)

        idempotency_store = RedisIdempotencyStore(settings.redis_url)
        await idempotency_store.connect()

        try:
            # Use cases
            process_payment_uc = ProcessPayment(
                payment_repository=payment_repo,
                transaction_repository=transaction_repo,
                payment_provider=payment_provider,
                event_publisher=event_publisher,
                idempotency_store=idempotency_store,
                outbox_repository=outbox_repo,
            )

            # Handler
            handler = CommandHandler(
                process_payment_use_case=process_payment_uc,
            )

            # Consumer
            consumer = RabbitMQCommandConsumer(settings.rabbitmq_url)
            await consumer.connect()

            # Worker
            worker = CommandWorker(
                consumer=consumer,
                handler=handler,
                queue_name="payment.commands.process",
            )

            await worker.start()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await consumer.disconnect()
            await event_publisher.disconnect()
            await idempotency_store.disconnect()
            await engine.dispose()

    logger.info("Command Worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        sys.exit(0)

"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from arch_hexagonal_postgresql_fast.adapters.api.fastapi_app import app_state
from arch_hexagonal_postgresql_fast.adapters.database.postgresql_outbox_repository import (
    PostgreSQLOutboxRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.postgresql_payment_repository import (
    PostgreSQLPaymentRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.postgresql_transaction_repository import (
    PostgreSQLTransactionRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.event_publisher import (
    EventPublisher,
)
from arch_hexagonal_postgresql_fast.application.ports.idempotency_store import (
    IdempotencyStore,
)
from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.payment_provider import (
    PaymentProvider,
)
from arch_hexagonal_postgresql_fast.application.ports.payment_repository import (
    PaymentRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.transaction_repository import (
    TransactionRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Get database session."""
    async with app_state.session_maker() as session:
        yield session


async def get_payment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PaymentRepository:
    """Get payment repository."""
    return PostgreSQLPaymentRepository(session)


async def get_transaction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TransactionRepository:
    """Get transaction repository."""
    return PostgreSQLTransactionRepository(session)


async def get_outbox_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OutboxRepository:
    """Get outbox repository."""
    return PostgreSQLOutboxRepository(session)


async def get_payment_provider(provider: str = "stripe") -> PaymentProvider:
    """Get payment provider based on name."""
    if provider == "stripe" and app_state.stripe_adapter:
        return app_state.stripe_adapter
    if provider == "paypal" and app_state.paypal_adapter:
        return app_state.paypal_adapter
    # Fallback to default
    if app_state.stripe_adapter:
        return app_state.stripe_adapter
    if app_state.paypal_adapter:
        return app_state.paypal_adapter
    raise ValueError("No payment provider configured")


async def get_event_publisher() -> EventPublisher:
    """Get event publisher."""
    return app_state.event_publisher


async def get_idempotency_store() -> IdempotencyStore:
    """Get idempotency store."""
    return app_state.redis_store

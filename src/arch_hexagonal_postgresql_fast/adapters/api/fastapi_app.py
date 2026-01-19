"""FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from arch_hexagonal_postgresql_fast.adapters.database.session_outbox_repository import (
    SessionManagedOutboxRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.sqlalchemy_models import Base
from arch_hexagonal_postgresql_fast.adapters.idempotency.redis_store import (
    RedisIdempotencyStore,
)
from arch_hexagonal_postgresql_fast.adapters.messaging.rabbitmq_publisher import (
    RabbitMQEventPublisher,
)
from arch_hexagonal_postgresql_fast.adapters.payment_providers.mock_stripe_adapter import (
    MockStripeAdapter,
)
from arch_hexagonal_postgresql_fast.adapters.payment_providers.paypal_adapter import (
    PayPalAdapter,
)
from arch_hexagonal_postgresql_fast.adapters.payment_providers.stripe_adapter import (
    StripeAdapter,
)
from arch_hexagonal_postgresql_fast.application.services.outbox_publisher import (
    OutboxPublisherService,
)
from arch_hexagonal_postgresql_fast.config import Settings
from arch_hexagonal_postgresql_fast.workers.outbox_worker import OutboxWorker


class AppState:
    """Application state container."""

    def __init__(self) -> None:
        """Initialize app state."""
        self.settings: Settings
        self.engine: AsyncEngine
        self.session_maker: async_sessionmaker[AsyncSession]
        self.redis_store: RedisIdempotencyStore
        self.event_publisher: RabbitMQEventPublisher
        self.stripe_adapter: StripeAdapter | MockStripeAdapter | None = None
        self.paypal_adapter: PayPalAdapter | None = None
        self.outbox_worker: OutboxWorker | None = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for startup/shutdown."""
    # Startup
    app_state.settings = Settings()

    # Database
    app_state.engine = create_async_engine(
        app_state.settings.database_url,
        echo=app_state.settings.debug,
    )
    app_state.session_maker = async_sessionmaker(
        app_state.engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with app_state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Redis
    app_state.redis_store = RedisIdempotencyStore(app_state.settings.redis_url)
    await app_state.redis_store.connect()

    # RabbitMQ
    app_state.event_publisher = RabbitMQEventPublisher(app_state.settings.rabbitmq_url)
    await app_state.event_publisher.connect()

    # Payment providers
    if app_state.settings.stripe_enabled:
        app_state.stripe_adapter = StripeAdapter(app_state.settings.stripe_api_key)
    else:
        # Use mock adapter for testing
        app_state.stripe_adapter = MockStripeAdapter()

    if app_state.settings.paypal_enabled:
        app_state.paypal_adapter = PayPalAdapter(
            client_id=app_state.settings.paypal_client_id,
            client_secret=app_state.settings.paypal_client_secret,
            mode=app_state.settings.paypal_mode,
        )

    # Start outbox worker for background event publishing
    async def create_outbox_session() -> AsyncSession:
        return app_state.session_maker()

    outbox_repo = SessionManagedOutboxRepository(create_outbox_session)
    outbox_publisher = OutboxPublisherService(
        outbox_repo=outbox_repo,
        event_publisher=app_state.event_publisher,
    )
    app_state.outbox_worker = OutboxWorker(
        publisher_service=outbox_publisher,
        interval_seconds=5,
    )
    await app_state.outbox_worker.start()

    yield

    # Shutdown
    if app_state.outbox_worker:
        await app_state.outbox_worker.stop()
    await app_state.redis_store.disconnect()
    await app_state.event_publisher.disconnect()
    await app_state.engine.dispose()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    from arch_hexagonal_postgresql_fast.adapters.api.routes import router
    from arch_hexagonal_postgresql_fast.adapters.api.routes_async import (
        router as async_router,
    )
    from arch_hexagonal_postgresql_fast.feature_flags import FeatureFlags

    app = FastAPI(
        title="Payment Service API",
        description="Hexagonal architecture payment processing service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # V1 routes (synchronous, backward compatible) - already has /api/v1 prefix in router
    app.include_router(router)

    # V2 routes (asynchronous, command-based) - has /v2 prefix
    if FeatureFlags.ENABLE_ASYNC_COMMANDS:
        app.include_router(async_router)

    # Log feature flags
    FeatureFlags.log_status()

    return app


app = create_app()

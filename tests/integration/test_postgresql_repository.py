"""Integration tests for PostgreSQL repository."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from arch_hexagonal_postgresql_fast.adapters.database.postgresql_payment_repository import (
    PostgreSQLPaymentRepository,
)
from arch_hexagonal_postgresql_fast.adapters.database.sqlalchemy_models import Base
from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)


@pytest.fixture
async def db_session(postgres_container: object) -> AsyncSession:
    """Create database session with testcontainer."""
    url = postgres_container.get_connection_url().replace(
        "psycopg2", "asyncpg"
    )
    
    engine = create_async_engine(url)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, class_=AsyncSession)
    
    async with session_maker() as session:
        yield session
    
    await engine.dispose()


class TestPostgreSQLPaymentRepository:
    """Test PostgreSQL payment repository."""

    async def test_save_and_get_payment(
        self, db_session: AsyncSession
    ) -> None:
        """Test saving and retrieving a payment."""
        repo = PostgreSQLPaymentRepository(db_session)
        
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        
        await repo.save(payment)
        
        retrieved = await repo.get_by_id("pay_123")
        assert retrieved is not None
        assert retrieved.id == "pay_123"
        assert retrieved.customer_id == "cus_123"
        assert retrieved.amount.value == Decimal("100.00")

    async def test_get_nonexistent_payment(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting a nonexistent payment."""
        repo = PostgreSQLPaymentRepository(db_session)
        
        result = await repo.get_by_id("nonexistent")
        assert result is None

    async def test_get_by_customer_id(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting payments by customer ID."""
        repo = PostgreSQLPaymentRepository(db_session)
        
        # Create two payments for same customer
        payment1 = Payment(
            id="pay_1",
            customer_id="cus_123",
            amount=Amount(value=Decimal("50.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment2 = Payment(
            id="pay_2",
            customer_id="cus_123",
            amount=Amount(value=Decimal("75.00"), currency="USD"),
            payment_method=PaymentMethod.PAYPAL,
            provider="paypal",
        )
        
        await repo.save(payment1)
        await repo.save(payment2)
        
        payments = await repo.get_by_customer_id("cus_123")
        assert len(payments) >= 2

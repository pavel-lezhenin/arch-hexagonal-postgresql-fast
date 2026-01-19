"""PostgreSQL payment repository implementation."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arch_hexagonal_postgresql_fast.adapters.database.sqlalchemy_models import (
    PaymentModel,
)
from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


class PostgreSQLPaymentRepository:
    """PostgreSQL implementation of payment repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self._session = session

    async def save(self, payment: Payment) -> None:
        """Save or update a payment."""
        model = await self._session.get(PaymentModel, payment.id)
        
        if model:
            # Update existing
            model.customer_id = payment.customer_id
            model.amount_value = payment.amount.value
            model.amount_currency = payment.amount.currency
            model.payment_method = payment.payment_method.value
            model.provider = payment.provider
            model.status = payment.status.value
            model.provider_transaction_id = payment.provider_transaction_id
            model.refunded_amount_value = (
                payment.refunded_amount.value
                if payment.refunded_amount
                else Decimal("0.00")
            )
            model.refunded_amount_currency = payment.amount.currency
            model.updated_at = payment.updated_at
            model.metadata = payment.metadata
        else:
            # Create new
            model = PaymentModel(
                id=payment.id,
                customer_id=payment.customer_id,
                amount_value=payment.amount.value,
                amount_currency=payment.amount.currency,
                payment_method=payment.payment_method.value,
                provider=payment.provider,
                status=payment.status.value,
                provider_transaction_id=payment.provider_transaction_id,
                refunded_amount_value=(
                    payment.refunded_amount.value
                    if payment.refunded_amount
                    else Decimal("0.00")
                ),
                refunded_amount_currency=payment.amount.currency,
                created_at=payment.created_at,
                updated_at=payment.updated_at,
                metadata=payment.metadata,
            )
            self._session.add(model)
        
        await self._session.commit()
        await self._session.refresh(model)

    async def get_by_id(self, payment_id: str) -> Payment | None:
        """Get payment by ID."""
        model = await self._session.get(PaymentModel, payment_id)
        if not model:
            return None
        return self._model_to_entity(model)

    async def get_by_customer_id(self, customer_id: str) -> list[Payment]:
        """Get all payments for a customer."""
        result = await self._session.execute(
            select(PaymentModel).where(
                PaymentModel.customer_id == customer_id
            )
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def delete(self, payment_id: str) -> None:
        """Delete a payment."""
        model = await self._session.get(PaymentModel, payment_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    def _model_to_entity(self, model: PaymentModel) -> Payment:
        """Convert database model to domain entity."""
        return Payment(
            id=model.id,
            customer_id=model.customer_id,
            amount=Amount(
                value=model.amount_value, currency=model.amount_currency
            ),
            payment_method=PaymentMethod(model.payment_method),
            provider=model.provider,
            status=TransactionStatus(model.status),
            provider_transaction_id=model.provider_transaction_id,
            refunded_amount=Amount(
                value=model.refunded_amount_value,
                currency=model.refunded_amount_currency,
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata,
        )

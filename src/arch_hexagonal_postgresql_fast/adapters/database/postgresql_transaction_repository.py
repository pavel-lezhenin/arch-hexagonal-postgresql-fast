"""PostgreSQL transaction repository implementation."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arch_hexagonal_postgresql_fast.adapters.database.sqlalchemy_models import (
    TransactionModel,
)
from arch_hexagonal_postgresql_fast.domain.entities.transaction import (
    Transaction,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


class PostgreSQLTransactionRepository:
    """PostgreSQL implementation of transaction repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self._session = session

    async def save(self, transaction: Transaction) -> None:
        """Save a transaction."""
        model = await self._session.get(TransactionModel, transaction.id)
        
        if model:
            # Update existing
            model.payment_id = transaction.payment_id
            model.amount_value = transaction.amount.value
            model.amount_currency = transaction.amount.currency
            model.transaction_type = transaction.transaction_type
            model.status = transaction.status.value
            model.provider = transaction.provider
            model.provider_transaction_id = (
                transaction.provider_transaction_id
            )
            model.error_message = transaction.error_message
            model.metadata = transaction.metadata
        else:
            # Create new
            model = TransactionModel(
                id=transaction.id,
                payment_id=transaction.payment_id,
                amount_value=transaction.amount.value,
                amount_currency=transaction.amount.currency,
                transaction_type=transaction.transaction_type,
                status=transaction.status.value,
                provider=transaction.provider,
                provider_transaction_id=transaction.provider_transaction_id,
                error_message=transaction.error_message,
                created_at=transaction.created_at,
                metadata=transaction.metadata,
            )
            self._session.add(model)
        
        await self._session.commit()
        await self._session.refresh(model)

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Get transaction by ID."""
        model = await self._session.get(TransactionModel, transaction_id)
        if not model:
            return None
        return self._model_to_entity(model)

    async def get_by_payment_id(
        self, payment_id: str
    ) -> list[Transaction]:
        """Get all transactions for a payment."""
        result = await self._session.execute(
            select(TransactionModel)
            .where(TransactionModel.payment_id == payment_id)
            .order_by(TransactionModel.created_at)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def get_by_provider_transaction_id(
        self, provider_transaction_id: str
    ) -> Transaction | None:
        """Get transaction by provider transaction ID."""
        result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.provider_transaction_id
                == provider_transaction_id
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)

    def _model_to_entity(self, model: TransactionModel) -> Transaction:
        """Convert database model to domain entity."""
        return Transaction(
            id=model.id,
            payment_id=model.payment_id,
            amount=Amount(
                value=model.amount_value, currency=model.amount_currency
            ),
            transaction_type=model.transaction_type,
            status=TransactionStatus(model.status),
            provider=model.provider,
            provider_transaction_id=model.provider_transaction_id,
            error_message=model.error_message,
            created_at=model.created_at,
            metadata=model.metadata,
        )

"""Process payment use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from arch_hexagonal_postgresql_fast.application.ports.event_publisher import (
    EventPublisher,
)
from arch_hexagonal_postgresql_fast.application.ports.idempotency_store import (
    IdempotencyStore,
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
from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
from arch_hexagonal_postgresql_fast.domain.entities.transaction import (
    Transaction,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@dataclass
class ProcessPaymentRequest:
    """Request to process a payment."""

    customer_id: str
    amount: Amount
    payment_method: PaymentMethod
    payment_method_token: str
    idempotency_key: str
    metadata: dict[str, str] | None = None


@dataclass
class ProcessPaymentResponse:
    """Response from processing a payment."""

    payment_id: str
    status: str
    provider_transaction_id: str | None
    created_at: datetime


class ProcessPayment:
    """Use case for processing a payment."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        transaction_repository: TransactionRepository,
        payment_provider: PaymentProvider,
        event_publisher: EventPublisher,
        idempotency_store: IdempotencyStore,
    ) -> None:
        """Initialize use case with dependencies."""
        self._payment_repo = payment_repository
        self._transaction_repo = transaction_repository
        self._provider = payment_provider
        self._events = event_publisher
        self._idempotency = idempotency_store

    async def execute(
        self, request: ProcessPaymentRequest
    ) -> ProcessPaymentResponse:
        """Execute the payment processing use case."""
        # Check idempotency
        if await self._idempotency.is_duplicate(request.idempotency_key):
            cached = await self._idempotency.get_result(
                request.idempotency_key
            )
            if cached:
                return ProcessPaymentResponse(**cached)

        # Create payment entity
        payment_id = str(uuid.uuid4())
        payment = Payment(
            id=payment_id,
            customer_id=request.customer_id,
            amount=request.amount,
            payment_method=request.payment_method,
            provider=self._provider.name,
            status=TransactionStatus.PENDING,
            metadata=request.metadata or {},
        )

        # Save payment
        await self._payment_repo.save(payment)
        await self._events.publish_payment_created(payment)

        try:
            # Call payment provider
            provider_tx_id = await self._provider.charge(
                amount=request.amount,
                payment_method_token=request.payment_method_token,
                idempotency_key=request.idempotency_key,
                customer_id=request.customer_id,
                metadata=request.metadata,
            )

            # Mark as processing
            payment.mark_processing(provider_tx_id)
            await self._payment_repo.save(payment)

            # Create transaction record
            transaction = Transaction(
                id=str(uuid.uuid4()),
                payment_id=payment.id,
                amount=request.amount,
                transaction_type="charge",
                status=TransactionStatus.PROCESSING,
                provider=self._provider.name,
                provider_transaction_id=provider_tx_id,
            )
            await self._transaction_repo.save(transaction)

            # Mark as completed
            payment.mark_completed()
            transaction.status = TransactionStatus.COMPLETED
            await self._payment_repo.save(payment)
            await self._transaction_repo.save(transaction)

            # Publish success event
            await self._events.publish_payment_completed(payment)

            response = ProcessPaymentResponse(
                payment_id=payment.id,
                status=payment.status.value,
                provider_transaction_id=provider_tx_id,
                created_at=payment.created_at,
            )

            # Cache result
            await self._idempotency.store_result(
                request.idempotency_key,
                {
                    "payment_id": response.payment_id,
                    "status": response.status,
                    "provider_transaction_id": response.provider_transaction_id,
                    "created_at": response.created_at.isoformat(),
                },
            )

            return response

        except Exception as e:
            # Mark as failed
            payment.mark_failed()
            await self._payment_repo.save(payment)

            # Create failed transaction
            failed_tx = Transaction(
                id=str(uuid.uuid4()),
                payment_id=payment.id,
                amount=request.amount,
                transaction_type="charge",
                status=TransactionStatus.FAILED,
                provider=self._provider.name,
                error_message=str(e),
            )
            await self._transaction_repo.save(failed_tx)

            # Publish failure event
            await self._events.publish_payment_failed(payment, str(e))

            raise

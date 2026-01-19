"""Refund payment use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

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
from arch_hexagonal_postgresql_fast.domain.entities.transaction import (
    Transaction,
)
from arch_hexagonal_postgresql_fast.domain.exceptions import PaymentNotFoundError
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@dataclass
class RefundPaymentRequest:
    """Request to refund a payment."""

    payment_id: str
    amount: Amount | None = None  # None for full refund
    idempotency_key: str | None = None


@dataclass
class RefundPaymentResponse:
    """Response from refunding a payment."""

    payment_id: str
    refund_amount: str
    status: str
    refund_transaction_id: str
    created_at: datetime


class RefundPayment:
    """Use case for refunding a payment."""

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
        self, request: RefundPaymentRequest
    ) -> RefundPaymentResponse:
        """Execute the refund use case."""
        # Check idempotency
        idempotency_key = request.idempotency_key or str(uuid.uuid4())
        if await self._idempotency.is_duplicate(idempotency_key):
            cached = await self._idempotency.get_result(idempotency_key)
            if cached:
                return RefundPaymentResponse(**cached)

        # Get payment
        payment = await self._payment_repo.get_by_id(request.payment_id)
        if not payment:
            raise PaymentNotFoundError(
                f"Payment {request.payment_id} not found"
            )

        # Determine refund amount
        refund_amount = (
            request.amount
            if request.amount
            else payment.remaining_refundable_amount()
        )

        # Validate can refund
        if not payment.can_be_refunded():
            raise ValueError(
                f"Payment {payment.id} cannot be refunded "
                f"(status: {payment.status})"
            )

        # Call provider
        if not payment.provider_transaction_id:
            raise ValueError(
                f"Payment {payment.id} has no provider transaction ID"
            )

        refund_tx_id = await self._provider.refund(
            provider_transaction_id=payment.provider_transaction_id,
            amount=refund_amount,
            idempotency_key=idempotency_key,
        )

        # Update payment
        payment.refund(refund_amount)
        await self._payment_repo.save(payment)

        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            payment_id=payment.id,
            amount=refund_amount,
            transaction_type="refund",
            status=TransactionStatus.COMPLETED,
            provider=self._provider.name,
            provider_transaction_id=refund_tx_id,
        )
        await self._transaction_repo.save(transaction)

        # Publish event
        await self._events.publish_payment_refunded(
            payment, str(refund_amount)
        )

        response = RefundPaymentResponse(
            payment_id=payment.id,
            refund_amount=str(refund_amount),
            status=payment.status.value,
            refund_transaction_id=refund_tx_id,
            created_at=transaction.created_at,
        )

        # Cache result
        await self._idempotency.store_result(
            idempotency_key,
            {
                "payment_id": response.payment_id,
                "refund_amount": response.refund_amount,
                "status": response.status,
                "refund_transaction_id": response.refund_transaction_id,
                "created_at": response.created_at.isoformat(),
            },
        )

        return response

"""Get transaction status use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from arch_hexagonal_postgresql_fast.application.ports.payment_repository import (
    PaymentRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.transaction_repository import (
    TransactionRepository,
)
from arch_hexagonal_postgresql_fast.domain.exceptions import PaymentNotFoundError


@dataclass
class GetTransactionStatusRequest:
    """Request to get transaction status."""

    payment_id: str


@dataclass
class TransactionInfo:
    """Transaction information."""

    id: str
    type: str
    amount: str
    status: str
    provider_transaction_id: str | None
    created_at: datetime


@dataclass
class GetTransactionStatusResponse:
    """Response with transaction status."""

    payment_id: str
    customer_id: str
    total_amount: str
    refunded_amount: str
    status: str
    transactions: list[TransactionInfo]


class GetTransactionStatus:
    """Use case for getting transaction status."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        """Initialize use case with dependencies."""
        self._payment_repo = payment_repository
        self._transaction_repo = transaction_repository

    async def execute(self, request: GetTransactionStatusRequest) -> GetTransactionStatusResponse:
        """Execute the get status use case."""
        # Get payment
        payment = await self._payment_repo.get_by_id(request.payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {request.payment_id} not found")

        # Get all transactions for this payment
        transactions = await self._transaction_repo.get_by_payment_id(request.payment_id)

        transaction_infos = [
            TransactionInfo(
                id=tx.id,
                type=tx.transaction_type,
                amount=str(tx.amount),
                status=tx.status.value,
                provider_transaction_id=tx.provider_transaction_id,
                created_at=tx.created_at,
            )
            for tx in transactions
        ]

        return GetTransactionStatusResponse(
            payment_id=payment.id,
            customer_id=payment.customer_id,
            total_amount=str(payment.amount),
            refunded_amount=str(payment.refunded_amount),
            status=payment.status.value,
            transactions=transaction_infos,
        )

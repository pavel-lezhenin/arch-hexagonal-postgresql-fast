"""Payment entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from arch_hexagonal_postgresql_fast.domain.exceptions import (
    InvalidPaymentStateError,
    RefundExceedsOriginalError,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@dataclass
class Payment:
    """Payment aggregate root."""

    id: str
    customer_id: str
    amount: Amount
    payment_method: PaymentMethod
    provider: str
    status: TransactionStatus = TransactionStatus.PENDING
    provider_transaction_id: str | None = None
    refunded_amount: Amount = field(default_factory=lambda: Amount.zero())
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate payment data."""
        if not self.id:
            raise ValueError("Payment ID is required")
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if not self.provider:
            raise ValueError("Payment provider is required")

        # Ensure refunded_amount has same currency as payment
        if self.refunded_amount.currency != self.amount.currency:
            object.__setattr__(self, "refunded_amount", Amount.zero(currency=self.amount.currency))

    def mark_processing(self, provider_transaction_id: str) -> None:
        """Mark payment as processing."""
        if self.status != TransactionStatus.PENDING:
            raise InvalidPaymentStateError(
                f"Cannot mark as processing: current status is {self.status}"
            )
        self.status = TransactionStatus.PROCESSING
        self.provider_transaction_id = provider_transaction_id
        self.updated_at = datetime.now(UTC)

    def mark_completed(self) -> None:
        """Mark payment as completed."""
        if self.status != TransactionStatus.PROCESSING:
            raise InvalidPaymentStateError(
                f"Cannot mark as completed: current status is {self.status}"
            )
        self.status = TransactionStatus.COMPLETED
        self.updated_at = datetime.now(UTC)

    def mark_failed(self) -> None:
        """Mark payment as failed."""
        if self.status in {
            TransactionStatus.COMPLETED,
            TransactionStatus.REFUNDED,
        }:
            raise InvalidPaymentStateError(
                f"Cannot mark as failed: current status is {self.status}"
            )
        self.status = TransactionStatus.FAILED
        self.updated_at = datetime.now(UTC)

    def refund(self, refund_amount: Amount) -> None:
        """Apply refund to payment."""
        if not self.status.can_refund():
            raise InvalidPaymentStateError(f"Cannot refund payment with status {self.status}")

        # Validate refund amount
        total_refunded = self.refunded_amount + refund_amount
        if total_refunded.value > self.amount.value:
            raise RefundExceedsOriginalError(
                f"Refund amount {total_refunded} exceeds original payment {self.amount}"
            )

        self.refunded_amount = total_refunded

        # Update status based on refund amount
        if self.refunded_amount.value == self.amount.value:
            self.status = TransactionStatus.REFUNDED
        else:
            self.status = TransactionStatus.PARTIALLY_REFUNDED

        self.updated_at = datetime.now(UTC)

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded."""
        return self.status.can_refund()

    def remaining_refundable_amount(self) -> Amount:
        """Calculate remaining amount that can be refunded."""
        if not self.can_be_refunded():
            return Amount.zero(currency=self.amount.currency)
        return self.amount - self.refunded_amount

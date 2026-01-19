"""Transaction entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@dataclass
class Transaction:
    """Transaction entity - represents a ledger entry."""

    id: str
    payment_id: str
    amount: Amount
    transaction_type: str  # "charge" or "refund"
    status: TransactionStatus
    provider: str
    provider_transaction_id: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate transaction data."""
        if not self.id:
            raise ValueError("Transaction ID is required")
        if not self.payment_id:
            raise ValueError("Payment ID is required")
        if self.transaction_type not in {"charge", "refund"}:
            raise ValueError(
                f"Invalid transaction type: {self.transaction_type}"
            )
        if not self.provider:
            raise ValueError("Provider is required")

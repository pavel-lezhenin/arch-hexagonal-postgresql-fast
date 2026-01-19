"""Transaction status enumeration."""

from __future__ import annotations

from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status types."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        """Check if status is terminal (cannot change)."""
        return self in {
            TransactionStatus.COMPLETED,
            TransactionStatus.FAILED,
            TransactionStatus.REFUNDED,
            TransactionStatus.CANCELLED,
        }

    def can_refund(self) -> bool:
        """Check if transaction can be refunded."""
        return self in {
            TransactionStatus.COMPLETED,
            TransactionStatus.PARTIALLY_REFUNDED,
        }

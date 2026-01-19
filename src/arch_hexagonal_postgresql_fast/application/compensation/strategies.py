"""Compensation strategies for failed operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment

logger = logging.getLogger(__name__)


class CompensationStrategy:
    """Base class for compensation strategies."""

    async def compensate(self, payment: Payment, error: Exception) -> None:
        """Execute compensation for failed payment.

        Args:
            payment: Payment entity to compensate
            error: Exception that caused the failure

        """
        raise NotImplementedError


class PaymentFailedCompensation(CompensationStrategy):
    """Compensation for permanently failed payments."""

    async def compensate(self, payment: Payment, error: Exception) -> None:
        """Mark payment as failed and log."""
        payment.mark_failed()
        logger.warning(
            "Payment %s permanently failed: %s (customer: %s)",
            payment.id,
            error,
            payment.customer_id,
        )
        # TODO: Send notification to customer
        # TODO: Create refund record if partially charged


class RetryableFailureCompensation(CompensationStrategy):
    """Compensation for temporary failures that should be retried."""

    async def compensate(self, payment: Payment, error: Exception) -> None:
        """Log retry attempt but keep payment in processing state."""
        logger.info(
            "Payment %s will be retried: %s (customer: %s)",
            payment.id,
            error,
            payment.customer_id,
        )
        # Payment stays in PROCESSING state for retry
        # Worker will retry based on message requeue


class FraudDetectedCompensation(CompensationStrategy):
    """Compensation for fraud-detected payments."""

    async def compensate(self, payment: Payment, error: Exception) -> None:
        """Mark payment as failed and flag for review."""
        payment.mark_failed()
        logger.error(
            "Payment %s flagged for fraud: %s (customer: %s)",
            payment.id,
            error,
            payment.customer_id,
        )
        # TODO: Send to fraud review queue
        # TODO: Notify security team

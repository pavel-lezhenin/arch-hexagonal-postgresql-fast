"""Test domain entities."""

from __future__ import annotations

from decimal import Decimal

import pytest

from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
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


class TestPayment:
    """Test Payment entity."""

    def test_create_payment(self) -> None:
        """Test creating a payment."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        assert payment.id == "pay_123"
        assert payment.status == TransactionStatus.PENDING

    def test_mark_processing(self) -> None:
        """Test marking payment as processing."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment.mark_processing("tx_123")
        assert payment.status == TransactionStatus.PROCESSING
        assert payment.provider_transaction_id == "tx_123"

    def test_mark_completed(self) -> None:
        """Test marking payment as completed."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment.mark_processing("tx_123")
        payment.mark_completed()
        assert payment.status == TransactionStatus.COMPLETED

    def test_cannot_mark_completed_if_not_processing(self) -> None:
        """Test that payment must be processing before completion."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        with pytest.raises(InvalidPaymentStateError):
            payment.mark_completed()

    def test_refund_full_amount(self) -> None:
        """Test full refund."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment.mark_processing("tx_123")
        payment.mark_completed()

        payment.refund(Amount(value=Decimal("100.00"), currency="USD"))
        assert payment.status == TransactionStatus.REFUNDED
        assert payment.refunded_amount.value == Decimal("100.00")

    def test_refund_partial_amount(self) -> None:
        """Test partial refund."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment.mark_processing("tx_123")
        payment.mark_completed()

        payment.refund(Amount(value=Decimal("30.00"), currency="USD"))
        assert payment.status == TransactionStatus.PARTIALLY_REFUNDED
        assert payment.refunded_amount.value == Decimal("30.00")

    def test_cannot_refund_more_than_original(self) -> None:
        """Test that refund cannot exceed original amount."""
        payment = Payment(
            id="pay_123",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
        )
        payment.mark_processing("tx_123")
        payment.mark_completed()

        with pytest.raises(RefundExceedsOriginalError):
            payment.refund(Amount(value=Decimal("150.00"), currency="USD"))

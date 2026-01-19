"""Test domain value objects."""

from __future__ import annotations

from decimal import Decimal

import pytest

from arch_hexagonal_postgresql_fast.domain.exceptions import InvalidAmountError
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


class TestAmount:
    """Test Amount value object."""

    def test_create_valid_amount(self) -> None:
        """Test creating a valid amount."""
        amount = Amount(value=Decimal("100.50"), currency="USD")
        assert amount.value == Decimal("100.50")
        assert amount.currency == "USD"

    def test_amount_must_be_positive(self) -> None:
        """Test that amount must be positive."""
        with pytest.raises(InvalidAmountError):
            Amount(value=Decimal("-10.00"), currency="USD")

    def test_currency_must_be_3_letters(self) -> None:
        """Test that currency must be 3 letters."""
        with pytest.raises(InvalidAmountError):
            Amount(value=Decimal("10.00"), currency="US")

    def test_amount_addition(self) -> None:
        """Test adding two amounts."""
        amount1 = Amount(value=Decimal("50.00"), currency="USD")
        amount2 = Amount(value=Decimal("30.00"), currency="USD")
        result = amount1 + amount2
        assert result.value == Decimal("80.00")

    def test_amount_subtraction(self) -> None:
        """Test subtracting two amounts."""
        amount1 = Amount(value=Decimal("50.00"), currency="USD")
        amount2 = Amount(value=Decimal("30.00"), currency="USD")
        result = amount1 - amount2
        assert result.value == Decimal("20.00")

    def test_to_cents(self) -> None:
        """Test converting amount to cents."""
        amount = Amount(value=Decimal("10.50"), currency="USD")
        assert amount.to_cents() == 1050

    def test_from_cents(self) -> None:
        """Test creating amount from cents."""
        amount = Amount.from_cents(1050, "USD")
        assert amount.value == Decimal("10.50")


class TestPaymentMethod:
    """Test PaymentMethod enum."""

    def test_payment_methods_exist(self) -> None:
        """Test that payment methods are defined."""
        assert PaymentMethod.CREDIT_CARD == "credit_card"
        assert PaymentMethod.DEBIT_CARD == "debit_card"
        assert PaymentMethod.PAYPAL == "paypal"


class TestTransactionStatus:
    """Test TransactionStatus enum."""

    def test_terminal_statuses(self) -> None:
        """Test terminal status detection."""
        assert TransactionStatus.COMPLETED.is_terminal()
        assert TransactionStatus.FAILED.is_terminal()
        assert not TransactionStatus.PENDING.is_terminal()

    def test_can_refund(self) -> None:
        """Test refund eligibility."""
        assert TransactionStatus.COMPLETED.can_refund()
        assert not TransactionStatus.PENDING.can_refund()

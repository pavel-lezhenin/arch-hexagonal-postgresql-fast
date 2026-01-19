"""Test get transaction status use case."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from arch_hexagonal_postgresql_fast.application.use_cases.get_transaction_status import (
    GetTransactionStatus,
    GetTransactionStatusRequest,
)
from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
from arch_hexagonal_postgresql_fast.domain.entities.transaction import Transaction
from arch_hexagonal_postgresql_fast.domain.exceptions import PaymentNotFoundError
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@pytest.fixture
def mock_payment_repo() -> Mock:
    """Create mock payment repository."""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_transaction_repo() -> Mock:
    """Create mock transaction repository."""
    repo = Mock()
    repo.get_by_payment_id = AsyncMock()
    return repo


@pytest.fixture
def sample_payment() -> Payment:
    """Create sample payment."""
    return Payment(
        id="pay_123",
        customer_id="cus_123",
        amount=Amount(value=Decimal("100.00"), currency="USD"),
        payment_method=PaymentMethod.CREDIT_CARD,
        provider="stripe",
    )


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """Create sample transactions."""
    return [
        Transaction(
            id="tx_1",
            payment_id="pay_123",
            transaction_type="charge",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            status=TransactionStatus.COMPLETED,
            provider="stripe",
            provider_transaction_id="stripe_tx_1",
            created_at=datetime.now(UTC),
        ),
    ]


class TestGetTransactionStatus:
    """Test GetTransactionStatus use case."""

    async def test_get_status_success(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        sample_payment: Payment,
        sample_transactions: list[Transaction],
    ) -> None:
        """Test getting transaction status successfully."""
        mock_payment_repo.get_by_id.return_value = sample_payment
        mock_transaction_repo.get_by_payment_id.return_value = sample_transactions

        use_case = GetTransactionStatus(mock_payment_repo, mock_transaction_repo)

        request = GetTransactionStatusRequest(payment_id="pay_123")
        response = await use_case.execute(request)

        assert response.payment_id == "pay_123"
        assert response.customer_id == "cus_123"
        assert len(response.transactions) == 1
        assert response.transactions[0].id == "tx_1"

    async def test_get_status_payment_not_found(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
    ) -> None:
        """Test error when payment not found."""
        mock_payment_repo.get_by_id.return_value = None

        use_case = GetTransactionStatus(mock_payment_repo, mock_transaction_repo)

        request = GetTransactionStatusRequest(payment_id="non_existent")
        with pytest.raises(PaymentNotFoundError):
            await use_case.execute(request)

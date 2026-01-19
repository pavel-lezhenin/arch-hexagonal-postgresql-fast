"""Test process payment use case."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from arch_hexagonal_postgresql_fast.application.use_cases.process_payment import (
    ProcessPayment,
    ProcessPaymentRequest,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)


@pytest.fixture
def mock_payment_repo() -> Mock:
    """Create mock payment repository."""
    repo = Mock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_transaction_repo() -> Mock:
    """Create mock transaction repository."""
    repo = Mock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_provider() -> Mock:
    """Create mock payment provider."""
    provider = Mock()
    provider.name = "stripe"
    provider.charge = AsyncMock(return_value="tx_123")
    return provider


@pytest.fixture
def mock_events() -> Mock:
    """Create mock event publisher."""
    events = Mock()
    events.publish_payment_created = AsyncMock()
    events.publish_payment_completed = AsyncMock()
    events.publish_payment_failed = AsyncMock()
    return events


@pytest.fixture
def mock_idempotency() -> Mock:
    """Create mock idempotency store."""
    store = Mock()
    store.is_duplicate = AsyncMock(return_value=False)
    store.store_result = AsyncMock()
    return store


@pytest.fixture
def mock_outbox_repo() -> Mock:
    """Create mock outbox repository."""
    repo = Mock()
    repo.save = AsyncMock()
    repo.get_unpublished = AsyncMock(return_value=[])
    return repo


class TestProcessPayment:
    """Test ProcessPayment use case."""

    async def test_process_payment_success(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test successful payment processing."""
        use_case = ProcessPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = ProcessPaymentRequest(
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_method_token="tok_123",
            idempotency_key="idem_123",
        )

        result = await use_case.execute(request)

        assert result.status == "completed"
        assert result.provider_transaction_id == "tx_123"
        assert mock_provider.charge.called
        assert mock_payment_repo.save.call_count >= 1
        # Events now saved to outbox instead of direct publishing
        assert mock_outbox_repo.save.call_count >= 2  # Created + Completed

    async def test_process_payment_with_idempotency(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test payment processing with idempotency check."""
        # Setup duplicate
        mock_idempotency.is_duplicate = AsyncMock(return_value=True)
        mock_idempotency.get_result = AsyncMock(
            return_value={
                "payment_id": "pay_123",
                "status": "completed",
                "provider_transaction_id": "tx_123",
                "created_at": "2026-01-19T00:00:00",
            }
        )

        use_case = ProcessPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = ProcessPaymentRequest(
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_method_token="tok_123",
            idempotency_key="idem_123",
        )

        result = await use_case.execute(request)

        assert result.payment_id == "pay_123"
        assert not mock_provider.charge.called

    async def test_process_payment_failure(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test payment processing failure."""
        # Make provider fail
        mock_provider.charge = AsyncMock(side_effect=Exception("Payment failed"))

        use_case = ProcessPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = ProcessPaymentRequest(
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_method_token="tok_123",
            idempotency_key="idem_123",
        )

        with pytest.raises(Exception, match="Payment failed"):
            await use_case.execute(request)

        # Failure event saved to outbox instead of direct publishing
        assert mock_outbox_repo.save.call_count >= 2  # Created + Failed

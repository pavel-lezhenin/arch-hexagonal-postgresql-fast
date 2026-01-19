"""Test refund payment use case."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from arch_hexagonal_postgresql_fast.application.use_cases.refund_payment import (
    RefundPayment,
    RefundPaymentRequest,
)
from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment
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
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
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
    provider.refund = AsyncMock(return_value="refund_tx_123")
    return provider


@pytest.fixture
def mock_events() -> Mock:
    """Create mock event publisher."""
    events = Mock()
    events.publish_payment_refunded = AsyncMock()
    return events


@pytest.fixture
def mock_idempotency() -> Mock:
    """Create mock idempotency store."""
    store = Mock()
    store.is_duplicate = AsyncMock(return_value=False)
    store.get_result = AsyncMock(return_value=None)
    store.store_result = AsyncMock()
    return store


@pytest.fixture
def mock_outbox_repo() -> Mock:
    """Create mock outbox repository."""
    repo = Mock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def completed_payment() -> Payment:
    """Create a completed payment for refund tests."""
    return Payment(
        id="pay_123",
        customer_id="cus_123",
        amount=Amount(value=Decimal("100.00"), currency="USD"),
        payment_method=PaymentMethod.CREDIT_CARD,
        provider="stripe",
        status=TransactionStatus.COMPLETED,
        provider_transaction_id="tx_123",
    )


class TestRefundPayment:
    """Test RefundPayment use case."""

    async def test_full_refund_success(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
        completed_payment: Payment,
    ) -> None:
        """Test successful full refund."""
        mock_payment_repo.get_by_id = AsyncMock(return_value=completed_payment)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_123",
            amount=None,  # Full refund
            idempotency_key="idem_refund_123",
        )

        result = await use_case.execute(request)

        assert result.payment_id == "pay_123"
        assert result.refund_amount == "100.00 USD"
        assert result.status == "refunded"
        assert result.refund_transaction_id == "refund_tx_123"
        assert mock_provider.refund.called
        assert mock_payment_repo.save.called
        assert mock_transaction_repo.save.called
        # Event saved to outbox instead of direct publishing
        assert mock_outbox_repo.save.called

    async def test_partial_refund_success(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
        completed_payment: Payment,
    ) -> None:
        """Test successful partial refund."""
        mock_payment_repo.get_by_id = AsyncMock(return_value=completed_payment)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        partial_amount = Amount(value=Decimal("30.00"), currency="USD")
        request = RefundPaymentRequest(
            payment_id="pay_123",
            amount=partial_amount,
            idempotency_key="idem_partial_123",
        )

        result = await use_case.execute(request)

        assert result.payment_id == "pay_123"
        assert result.refund_amount == "30.00 USD"
        assert result.status == "partially_refunded"
        assert mock_provider.refund.called
        # Verify partial refund was called with correct amount
        call_args = mock_provider.refund.call_args
        assert call_args.kwargs["amount"] == partial_amount

    async def test_payment_not_found(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test refund when payment not found."""
        mock_payment_repo.get_by_id = AsyncMock(return_value=None)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_nonexistent",
            idempotency_key="idem_notfound_123",
        )

        with pytest.raises(PaymentNotFoundError, match="Payment pay_nonexistent not found"):
            await use_case.execute(request)

        assert not mock_provider.refund.called
        assert not mock_outbox_repo.save.called

    async def test_cannot_refund_pending_payment(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test refund fails for pending payment."""
        pending_payment = Payment(
            id="pay_pending",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
            status=TransactionStatus.PENDING,
        )
        mock_payment_repo.get_by_id = AsyncMock(return_value=pending_payment)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_pending",
            idempotency_key="idem_pending_123",
        )

        with pytest.raises(ValueError, match="cannot be refunded"):
            await use_case.execute(request)

        assert not mock_provider.refund.called

    async def test_cannot_refund_already_refunded_payment(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test refund fails for already fully refunded payment."""
        refunded_payment = Payment(
            id="pay_refunded",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
            status=TransactionStatus.REFUNDED,
            provider_transaction_id="tx_123",
            refunded_amount=Amount(value=Decimal("100.00"), currency="USD"),
        )
        mock_payment_repo.get_by_id = AsyncMock(return_value=refunded_payment)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_refunded",
            idempotency_key="idem_already_123",
        )

        with pytest.raises(ValueError, match="cannot be refunded"):
            await use_case.execute(request)

        assert not mock_provider.refund.called

    async def test_refund_with_idempotency(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test refund returns cached result on duplicate request."""
        mock_idempotency.is_duplicate = AsyncMock(return_value=True)
        mock_idempotency.get_result = AsyncMock(
            return_value={
                "payment_id": "pay_123",
                "refund_amount": "100.00 USD",
                "status": "refunded",
                "refund_transaction_id": "refund_tx_123",
                "created_at": "2026-01-19T00:00:00",
            }
        )

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_123",
            idempotency_key="idem_duplicate_123",
        )

        result = await use_case.execute(request)

        assert result.payment_id == "pay_123"
        assert result.refund_amount == "100.00 USD"
        # Provider should not be called for duplicate
        assert not mock_provider.refund.called
        assert not mock_payment_repo.get_by_id.called

    async def test_payment_without_provider_transaction_id(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
    ) -> None:
        """Test refund fails when payment has no provider transaction ID."""
        payment_no_tx = Payment(
            id="pay_no_tx",
            customer_id="cus_123",
            amount=Amount(value=Decimal("100.00"), currency="USD"),
            payment_method=PaymentMethod.CREDIT_CARD,
            provider="stripe",
            status=TransactionStatus.COMPLETED,
            provider_transaction_id=None,
        )
        mock_payment_repo.get_by_id = AsyncMock(return_value=payment_no_tx)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_no_tx",
            idempotency_key="idem_no_tx_123",
        )

        with pytest.raises(ValueError, match="has no provider transaction ID"):
            await use_case.execute(request)

        assert not mock_provider.refund.called

    async def test_outbox_event_contains_correct_payload(
        self,
        mock_payment_repo: Mock,
        mock_transaction_repo: Mock,
        mock_provider: Mock,
        mock_events: Mock,
        mock_idempotency: Mock,
        mock_outbox_repo: Mock,
        completed_payment: Payment,
    ) -> None:
        """Test that outbox event contains correct refund payload."""
        mock_payment_repo.get_by_id = AsyncMock(return_value=completed_payment)

        use_case = RefundPayment(
            mock_payment_repo,
            mock_transaction_repo,
            mock_provider,
            mock_events,
            mock_idempotency,
            mock_outbox_repo,
        )

        request = RefundPaymentRequest(
            payment_id="pay_123",
            amount=None,
            idempotency_key="idem_payload_123",
        )

        await use_case.execute(request)

        # Verify outbox save was called
        assert mock_outbox_repo.save.called
        saved_event = mock_outbox_repo.save.call_args[0][0]

        assert saved_event.aggregate_type == "Payment"
        assert saved_event.aggregate_id == "pay_123"
        assert saved_event.event_type == "PaymentRefunded"
        assert saved_event.payload["payment_id"] == "pay_123"
        assert saved_event.payload["customer_id"] == "cus_123"
        assert saved_event.payload["refund_amount"] == "100.00 USD"
        assert saved_event.payload["currency"] == "USD"
        assert saved_event.payload["refund_transaction_id"] == "refund_tx_123"

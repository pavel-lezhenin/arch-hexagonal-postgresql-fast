"""Mock Stripe adapter for testing."""

from __future__ import annotations

from arch_hexagonal_postgresql_fast.application.ports.payment_provider import (
    PaymentProvider,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount


class MockStripeAdapter(PaymentProvider):
    """Mock Stripe payment provider for testing."""

    @property
    def name(self) -> str:
        """Provider name."""
        return "mock_stripe"

    async def charge(
        self,
        amount: Amount,
        payment_method_token: str,
        idempotency_key: str,
        customer_id: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Mock charge - always succeeds."""
        return f"mock_ch_{idempotency_key}"

    async def refund(
        self,
        provider_transaction_id: str,
        amount: Amount | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        """Mock refund - always succeeds."""
        return f"mock_re_{idempotency_key or 'auto'}"

    async def get_charge_status(self, provider_transaction_id: str) -> dict[str, str]:
        """Mock get charge status."""
        return {
            "id": provider_transaction_id,
            "status": "succeeded",
            "amount": "10000",
            "currency": "usd",
        }

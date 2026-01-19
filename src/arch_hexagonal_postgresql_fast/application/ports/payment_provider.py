"""Payment provider port."""

from __future__ import annotations

from typing import Protocol

from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount


class PaymentProvider(Protocol):
    """Interface for payment provider integrations."""

    @property
    def name(self) -> str:
        """Provider name (e.g., 'stripe', 'paypal')."""
        ...

    async def charge(
        self,
        amount: Amount,
        payment_method_token: str,
        idempotency_key: str,
        customer_id: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Charge a payment method.

        Args:
            amount: Amount to charge
            payment_method_token: Token representing payment method
            idempotency_key: Key to prevent duplicate charges
            customer_id: Customer identifier
            metadata: Additional metadata

        Returns:
            Provider transaction ID

        Raises:
            PaymentProviderError: If charge fails
        """
        ...

    async def refund(
        self,
        provider_transaction_id: str,
        amount: Amount | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        """
        Refund a charge.

        Args:
            provider_transaction_id: Original transaction ID
            amount: Amount to refund (None for full refund)
            idempotency_key: Key to prevent duplicate refunds

        Returns:
            Refund transaction ID

        Raises:
            PaymentProviderError: If refund fails
        """
        ...

    async def get_charge_status(
        self, provider_transaction_id: str
    ) -> dict[str, str]:
        """
        Get charge status from provider.

        Returns:
            Dictionary with status information
        """
        ...

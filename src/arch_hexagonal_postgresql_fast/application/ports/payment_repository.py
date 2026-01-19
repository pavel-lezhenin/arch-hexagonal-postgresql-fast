"""Payment repository port."""

from __future__ import annotations

from typing import Protocol

from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment


class PaymentRepository(Protocol):
    """Repository interface for payment persistence."""

    async def save(self, payment: Payment) -> None:
        """Save or update a payment."""
        ...

    async def get_by_id(self, payment_id: str) -> Payment | None:
        """Get payment by ID."""
        ...

    async def get_by_customer_id(self, customer_id: str) -> list[Payment]:
        """Get all payments for a customer."""
        ...

    async def delete(self, payment_id: str) -> None:
        """Delete a payment."""
        ...

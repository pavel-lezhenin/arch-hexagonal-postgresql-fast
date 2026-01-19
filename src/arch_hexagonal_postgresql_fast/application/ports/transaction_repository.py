"""Transaction repository port."""

from __future__ import annotations

from typing import Protocol

from arch_hexagonal_postgresql_fast.domain.entities.transaction import (
    Transaction,
)


class TransactionRepository(Protocol):
    """Repository interface for transaction persistence."""

    async def save(self, transaction: Transaction) -> None:
        """Save a transaction."""
        ...

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Get transaction by ID."""
        ...

    async def get_by_payment_id(self, payment_id: str) -> list[Transaction]:
        """Get all transactions for a payment."""
        ...

    async def get_by_provider_transaction_id(
        self, provider_transaction_id: str
    ) -> Transaction | None:
        """Get transaction by provider transaction ID."""
        ...

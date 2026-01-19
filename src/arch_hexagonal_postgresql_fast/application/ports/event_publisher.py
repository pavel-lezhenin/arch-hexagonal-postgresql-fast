"""Event publisher port."""

from __future__ import annotations

from typing import Protocol

from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment


class EventPublisher(Protocol):
    """Interface for publishing domain events."""

    async def publish_event(
        self,
        event_type: str,
        payload: dict[str, object],
        routing_key: str = "payments",
    ) -> None:
        """Publish a generic event to message queue.

        Args:
            event_type: Type of the event (e.g., 'PaymentCreated')
            payload: Event data as dictionary
            routing_key: Message routing key (default: 'payments')

        """
        ...

    async def publish_payment_created(self, payment: Payment) -> None:
        """Publish payment created event."""
        ...

    async def publish_payment_completed(self, payment: Payment) -> None:
        """Publish payment completed event."""
        ...

    async def publish_payment_failed(self, payment: Payment, error: str) -> None:
        """Publish payment failed event."""
        ...

    async def publish_payment_refunded(self, payment: Payment, refund_amount: str) -> None:
        """Publish payment refunded event."""
        ...

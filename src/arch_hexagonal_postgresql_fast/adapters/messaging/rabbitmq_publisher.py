"""RabbitMQ event publisher adapter."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import aio_pika

from arch_hexagonal_postgresql_fast.domain.entities.payment import Payment


class RabbitMQEventPublisher:
    """RabbitMQ implementation of event publisher."""

    def __init__(self, connection_url: str) -> None:
        """Initialize publisher with connection URL."""
        self._connection_url = connection_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        self._connection = await aio_pika.connect_robust(self._connection_url)
        self._channel = await self._connection.channel()

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()

    async def publish_event(
        self,
        event_type: str,
        payload: dict[str, object],
        routing_key: str = "payments",
    ) -> None:
        """Publish a generic event to RabbitMQ.

        Args:
            event_type: Type of the event (e.g., 'PaymentCreated')
            payload: Event data as dictionary
            routing_key: Message routing key

        """
        await self._publish_event(event_type, payload, routing_key)

    async def publish_payment_created(self, payment: Payment) -> None:
        """Publish payment created event."""
        await self._publish_event(
            "payment.created",
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": str(payment.amount),
                "status": payment.status.value,
            },
        )

    async def publish_payment_completed(self, payment: Payment) -> None:
        """Publish payment completed event."""
        await self._publish_event(
            "payment.completed",
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": str(payment.amount),
                "provider_transaction_id": payment.provider_transaction_id,
            },
        )

    async def publish_payment_failed(self, payment: Payment, error: str) -> None:
        """Publish payment failed event."""
        await self._publish_event(
            "payment.failed",
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": str(payment.amount),
                "error": error,
            },
        )

    async def publish_payment_refunded(self, payment: Payment, refund_amount: str) -> None:
        """Publish payment refunded event."""
        await self._publish_event(
            "payment.refunded",
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "original_amount": str(payment.amount),
                "refund_amount": refund_amount,
                "status": payment.status.value,
            },
        )

    async def _publish_event(
        self,
        event_type: str,
        data: dict[str, object],
        routing_key: str = "payments",
    ) -> None:
        """Publish an event to RabbitMQ.

        Args:
            event_type: Type of the event
            data: Event payload data
            routing_key: Message routing key

        """
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        event = {
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data,
        }

        message = aio_pika.Message(
            body=json.dumps(event, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._channel.default_exchange.publish(message, routing_key=routing_key)

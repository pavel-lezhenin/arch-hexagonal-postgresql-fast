"""RabbitMQ implementation of CommandPublisher."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aio_pika import DeliveryMode, Message, connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection

if TYPE_CHECKING:
    from arch_hexagonal_postgresql_fast.application.commands import (
        ProcessPaymentCommand,
        RefundPaymentCommand,
    )

logger = logging.getLogger(__name__)


class RabbitMQCommandPublisher:
    """RabbitMQ implementation of command publisher."""

    def __init__(self, rabbitmq_url: str) -> None:
        """Initialize publisher with RabbitMQ connection URL."""
        self._url = rabbitmq_url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        self._connection = await connect_robust(self._url)
        self._channel = await self._connection.channel()
        logger.info("RabbitMQ command publisher connected")

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()
        logger.info("RabbitMQ command publisher disconnected")

    async def publish_process_payment(
        self,
        command: ProcessPaymentCommand,
    ) -> None:
        """Publish process payment command to queue."""
        await self._publish(
            queue_name="payment.commands.process",
            command_type="ProcessPaymentCommand",
            payload={
                "command_id": command.command_id,
                "idempotency_key": command.idempotency_key,
                "timestamp": command.timestamp.isoformat(),
                "customer_id": command.customer_id,
                "amount": str(command.amount),
                "currency": command.currency,
                "payment_method": command.payment_method,
                "payment_method_token": command.payment_method_token,
                "metadata": command.metadata,
            },
        )

    async def publish_refund_payment(
        self,
        command: RefundPaymentCommand,
    ) -> None:
        """Publish refund payment command to queue."""
        await self._publish(
            queue_name="payment.commands.refund",
            command_type="RefundPaymentCommand",
            payload={
                "command_id": command.command_id,
                "idempotency_key": command.idempotency_key,
                "timestamp": command.timestamp.isoformat(),
                "payment_id": command.payment_id,
                "amount": str(command.amount) if command.amount else None,
                "reason": command.reason,
            },
        )

    async def _publish(
        self,
        queue_name: str,
        command_type: str,
        payload: dict[str, object],
    ) -> None:
        """Publish command to specified queue."""
        if not self._channel:
            msg = "Not connected to RabbitMQ"
            raise RuntimeError(msg)

        # Declare queue (idempotent)
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,  # Survive broker restart
        )

        # Create message
        message_body = json.dumps(
            {
                "command_type": command_type,
                "payload": payload,
            }
        ).encode()

        message = Message(
            body=message_body,
            delivery_mode=DeliveryMode.PERSISTENT,  # Persist to disk
            content_type="application/json",
        )

        # Publish to queue
        await self._channel.default_exchange.publish(
            message,
            routing_key=queue.name,
        )

        logger.info(
            "Published command %s to queue %s (idempotency_key=%s)",
            command_type,
            queue_name,
            payload.get("idempotency_key"),
        )

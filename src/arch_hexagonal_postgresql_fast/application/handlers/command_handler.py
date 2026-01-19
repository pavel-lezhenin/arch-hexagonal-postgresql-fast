"""Command handler for processing commands from RabbitMQ."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from arch_hexagonal_postgresql_fast.application.use_cases.process_payment import (
    ProcessPayment,
    ProcessPaymentRequest,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handler for processing commands from message queue."""

    def __init__(
        self,
        process_payment_use_case: ProcessPayment,
    ) -> None:
        """Initialize command handler with use cases."""
        self._process_payment = process_payment_use_case

    async def handle_message(self, message: AbstractIncomingMessage) -> None:
        """Handle incoming command message.

        Args:
            message: RabbitMQ message containing command

        """
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                command_type = body.get("command_type")
                payload = body.get("payload", {})

                logger.info(
                    "Processing command: %s (idempotency_key=%s)",
                    command_type,
                    payload.get("idempotency_key"),
                )

                # Route to appropriate handler
                if command_type == "ProcessPaymentCommand":
                    await self._handle_process_payment(payload)
                elif command_type == "RefundPaymentCommand":
                    await self._handle_refund_payment(payload)
                else:
                    logger.warning("Unknown command type: %s", command_type)

                logger.info(
                    "Command processed successfully: %s (idempotency_key=%s)",
                    command_type,
                    payload.get("idempotency_key"),
                )

            except Exception:
                logger.exception("Error processing command")
                # Message will be requeued by RabbitMQ
                raise

    async def _handle_process_payment(self, payload: dict[str, object]) -> None:
        """Handle ProcessPaymentCommand."""
        request = ProcessPaymentRequest(
            customer_id=str(payload["customer_id"]),
            amount=Amount(
                value=Decimal(str(payload["amount"])),
                currency=str(payload["currency"]),
            ),
            payment_method=PaymentMethod(str(payload["payment_method"])),
            payment_method_token=str(payload["payment_method_token"]),
            idempotency_key=str(payload["idempotency_key"]),
            metadata=payload.get("metadata") or {},  # type: ignore[arg-type]
        )

        await self._process_payment.execute(request)

    async def _handle_refund_payment(self, payload: dict[str, object]) -> None:
        """Handle RefundPaymentCommand."""
        # TODO: Implement refund use case handler
        logger.info("Refund command received: %s", payload.get("payment_id"))

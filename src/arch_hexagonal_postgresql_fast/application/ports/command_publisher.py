"""Command publisher port for sending commands to RabbitMQ."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from arch_hexagonal_postgresql_fast.application.commands import (
        ProcessPaymentCommand,
        RefundPaymentCommand,
    )


class CommandPublisher(Protocol):
    """Port for publishing commands to message queue."""

    async def publish_process_payment(
        self,
        command: ProcessPaymentCommand,
    ) -> None:
        """Publish process payment command.

        Args:
            command: ProcessPaymentCommand with payment details

        """
        ...

    async def publish_refund_payment(
        self,
        command: RefundPaymentCommand,
    ) -> None:
        """Publish refund payment command.

        Args:
            command: RefundPaymentCommand with refund details

        """
        ...

"""Command models for payment operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Command:
    """Base command with common fields."""

    command_id: str
    idempotency_key: str
    timestamp: datetime


@dataclass
class ProcessPaymentCommand(Command):
    """Command to process a payment."""

    customer_id: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_method_token: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class RefundPaymentCommand(Command):
    """Command to refund a payment."""

    payment_id: str
    amount: Decimal | None = None  # None = full refund
    reason: str = ""

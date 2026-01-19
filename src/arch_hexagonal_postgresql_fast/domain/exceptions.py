"""Domain exceptions."""

from __future__ import annotations


class DomainException(Exception):
    """Base exception for domain layer."""


class InvalidAmountError(DomainException):
    """Raised when amount is invalid (negative, zero, or wrong currency)."""


class PaymentNotFoundError(DomainException):
    """Raised when payment is not found."""


class InsufficientFundsError(DomainException):
    """Raised when customer has insufficient funds for payment."""


class InvalidPaymentStateError(DomainException):
    """Raised when payment is in invalid state for operation."""


class RefundExceedsOriginalError(DomainException):
    """Raised when refund amount exceeds original payment amount."""

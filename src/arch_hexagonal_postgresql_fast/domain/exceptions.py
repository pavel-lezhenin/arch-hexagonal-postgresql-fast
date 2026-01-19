"""Domain exceptions."""

from __future__ import annotations


class DomainException(Exception):
    """Base exception for domain layer."""

    pass


class InvalidAmountError(DomainException):
    """Raised when amount is invalid (negative, zero, or wrong currency)."""

    pass


class PaymentNotFoundError(DomainException):
    """Raised when payment is not found."""

    pass


class InsufficientFundsError(DomainException):
    """Raised when customer has insufficient funds for payment."""

    pass


class InvalidPaymentStateError(DomainException):
    """Raised when payment is in invalid state for operation."""

    pass


class RefundExceedsOriginalError(DomainException):
    """Raised when refund amount exceeds original payment amount."""

    pass

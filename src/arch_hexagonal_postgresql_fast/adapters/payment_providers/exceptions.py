"""Payment provider exceptions."""

from __future__ import annotations


class PaymentProviderError(Exception):
    """Base exception for payment provider errors."""


class InsufficientFundsError(PaymentProviderError):
    """Raised when customer has insufficient funds."""


class InvalidPaymentMethodError(PaymentProviderError):
    """Raised when payment method is invalid."""


class ProviderConnectionError(PaymentProviderError):
    """Raised when connection to provider fails."""

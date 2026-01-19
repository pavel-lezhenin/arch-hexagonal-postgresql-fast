"""Compensation package."""

from __future__ import annotations

from .strategies import (
    CompensationStrategy,
    FraudDetectedCompensation,
    PaymentFailedCompensation,
    RetryableFailureCompensation,
)

__all__ = [
    "CompensationStrategy",
    "FraudDetectedCompensation",
    "PaymentFailedCompensation",
    "RetryableFailureCompensation",
]
